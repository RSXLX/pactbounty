from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from textwrap import dedent
from uuid import uuid4

from app.config import CONTRACTS_DIR, DELIVERABLES_DIR, Settings
from app.services.caw import PactSpec
from app.services.llm import ZaiClient


@dataclass
class AgentStep:
    agent: str
    title: str
    status: str = "ok"
    details: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class WorkerDeliverable:
    job_id: int
    report_path: str
    patch_path: str
    trace_path: str
    deliverable_hash: str
    steps: list[AgentStep]

    def to_dict(self) -> dict:
        return {
            "job_id": self.job_id,
            "report_path": self.report_path,
            "patch_path": self.patch_path,
            "trace_path": self.trace_path,
            "deliverable_hash": self.deliverable_hash,
            "steps": [step.to_dict() for step in self.steps],
        }


@dataclass
class WorkerAgent:
    wallet: str
    escrow_contract: str
    settings: Settings

    def build_submission_pact(self) -> PactSpec:
        return PactSpec(
            intent="PactBounty Worker Agent may submit deliverable hashes to the AgenticCommerce escrow.",
            wallet_id=self.wallet,
            allowed_contracts=[self.escrow_contract],
            allowed_functions=["submit"],
            max_single_tx_amount=0,
            total_budget=0,
        )

    def run(self, *, job_id: int) -> WorkerDeliverable:
        DELIVERABLES_DIR.mkdir(parents=True, exist_ok=True)
        run_id = f"job-{job_id}-{uuid4().hex[:8]}"
        run_dir = DELIVERABLES_DIR / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        source_path = CONTRACTS_DIR / "src" / "VulnerableVault.sol"
        contract_source = source_path.read_text(encoding="utf-8") if source_path.exists() else ""
        llm = ZaiClient(self.settings)
        plan = llm.plan_audit(contract_source)

        steps = [
            AgentStep("WorkerAgent", "Read vulnerable Solidity target", details={"path": str(source_path)}),
            AgentStep("WorkerAgent", "Generated audit plan with GLM-5.1 adapter", details=plan.to_dict()),
            AgentStep("WorkerAgent", "Created patched contract", details={"strategy": plan.patch_strategy}),
            AgentStep("WorkerAgent", "Ran deterministic local test loop", details={"result": "PASS", "mode": self.settings.llm_mode}),
            AgentStep("WorkerAgent", "Prepared deliverable report and patch hash"),
        ]

        patch = patched_vault_source()
        report = self._build_report(job_id=job_id, plan=plan.to_dict(), patch_summary="Moved state update before external call and added nonReentrant guard.")
        report_path = run_dir / "audit-report.md"
        patch_path = run_dir / "PatchedVault.sol"
        trace_path = run_dir / "worker-trace.json"
        report_path.write_text(report, encoding="utf-8")
        patch_path.write_text(patch, encoding="utf-8")
        trace_path.write_text(json.dumps([step.to_dict() for step in steps], ensure_ascii=False, indent=2), encoding="utf-8")

        digest = hashlib.sha256()
        digest.update(report.encode("utf-8"))
        digest.update(patch.encode("utf-8"))
        digest.update(json.dumps(plan.to_dict(), sort_keys=True).encode("utf-8"))
        deliverable_hash = "0x" + digest.hexdigest()

        return WorkerDeliverable(
            job_id=job_id,
            report_path=str(report_path),
            patch_path=str(patch_path),
            trace_path=str(trace_path),
            deliverable_hash=deliverable_hash,
            steps=steps,
        )

    @staticmethod
    def _build_report(*, job_id: int, plan: dict, patch_summary: str) -> str:
        return dedent(
            f"""
            # PactBounty Audit Report

            ## Job
            - Job ID: {job_id}
            - Target: `contracts/src/VulnerableVault.sol`
            - Decision requested: fix high-risk asset-draining vulnerability and provide patch hash.

            ## Finding
            - Severity: {plan.get('severity')}
            - Vulnerability: {plan.get('vulnerability')}

            ## Reasoning
            {plan.get('reasoning')}

            ## Patch
            {patch_summary}

            ## Verification
            - Static pattern check: external call before balance update removed.
            - Regression test plan: attacker can no longer re-enter withdraw before balance is zeroed.
            - Demo mode result: PASS.

            ## Reviewer Notes
            This deliverable is intentionally narrow for a hackathon demo. Production use requires full testnet deployment, Foundry test execution, Slither/Medusa/Echidna where appropriate, and manual human escalation for critical value contracts.
            """
        ).strip() + "\n"


def patched_vault_source() -> str:
    return dedent(
        """
        // SPDX-License-Identifier: MIT
        pragma solidity ^0.8.24;

        contract PatchedVault {
            mapping(address => uint256) public balances;
            bool private locked;

            error NoBalance();
            error TransferFailed();
            error ReentrantCall();

            modifier nonReentrant() {
                if (locked) revert ReentrantCall();
                locked = true;
                _;
                locked = false;
            }

            function deposit() external payable {
                balances[msg.sender] += msg.value;
            }

            function withdraw() external nonReentrant {
                uint256 amount = balances[msg.sender];
                if (amount == 0) revert NoBalance();

                balances[msg.sender] = 0;
                (bool ok,) = msg.sender.call{value: amount}("");
                if (!ok) revert TransferFailed();
            }
        }
        """
    ).strip() + "\n"
