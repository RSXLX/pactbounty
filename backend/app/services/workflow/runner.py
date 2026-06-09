from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from time import time
from typing import Any

from app.agents import ClientAgent, EvaluatorAgent, WorkerAgent
from app.config import Settings
from app.services.caw import AuditEntry, CawCall, Ledger, MockCawClient, Pact, PolicyDenied
from app.services.caw.base import fake_tx_hash
from app.services.caw.real_caw_client import RealCawClient
from app.services.escrow import ESCROW_ADDRESS, EscrowService, JobRecord

MUSDC = 1_000_000
DEMO_BUDGET = 5 * MUSDC
DEMO_TOTAL_BUDGET = 6 * MUSDC


@dataclass
class DemoEvidence:
    chain_id: int
    mock_usdc: str
    agentic_commerce: str
    client_wallet: str
    worker_wallet: str
    evaluator_wallet: str
    job_id: int | None = None
    tx_hashes: list[str] = field(default_factory=list)
    denial: dict[str, Any] | None = None
    deliverable_hash: str | None = None
    reason_hash: str | None = None
    report_path: str | None = None
    patch_path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "chain_id": self.chain_id,
            "mock_usdc": self.mock_usdc,
            "agentic_commerce": self.agentic_commerce,
            "client_wallet": self.client_wallet,
            "worker_wallet": self.worker_wallet,
            "evaluator_wallet": self.evaluator_wallet,
            "job_id": self.job_id,
            "tx_hashes": self.tx_hashes,
            "denial": self.denial,
            "deliverable_hash": self.deliverable_hash,
            "reason_hash": self.reason_hash,
            "report_path": self.report_path,
            "patch_path": self.patch_path,
        }


class DemoWorkflow:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.ledger = Ledger()
        self.escrow = EscrowService()
        self.caw = MockCawClient() if settings.caw_mode.lower() == "mock" else RealCawClient(settings)
        self.client_agent = ClientAgent(
            wallet=settings.client_agent_wallet,
            mock_usdc=settings.mock_usdc_address,
            escrow_contract=settings.agentic_commerce_address,
        )
        self.worker_agent = WorkerAgent(
            wallet=settings.worker_agent_wallet,
            escrow_contract=settings.agentic_commerce_address,
            settings=settings,
        )
        self.evaluator_agent = EvaluatorAgent(
            wallet=settings.evaluator_agent_wallet,
            escrow_contract=settings.agentic_commerce_address,
        )
        self.last_evidence = DemoEvidence(
            chain_id=settings.chain_id,
            mock_usdc=settings.mock_usdc_address,
            agentic_commerce=settings.agentic_commerce_address,
            client_wallet=settings.client_agent_wallet,
            worker_wallet=settings.worker_agent_wallet,
            evaluator_wallet=settings.evaluator_agent_wallet,
        )
        self.last_steps: list[dict[str, Any]] = []
        self.last_pacts: list[Pact] = []

    def reset(self) -> dict[str, Any]:
        self.ledger.reset()
        self.escrow.reset()
        if isinstance(self.caw, MockCawClient):
            self.caw = MockCawClient()
        self.ledger.mint(self.settings.client_agent_wallet, 100 * MUSDC)
        self.ledger.mint(self.settings.worker_agent_wallet, 0)
        self.ledger.mint(self.settings.evaluator_agent_wallet, 0)
        self.ledger.mint(ESCROW_ADDRESS, 0)
        self.last_evidence = DemoEvidence(
            chain_id=self.settings.chain_id,
            mock_usdc=self.settings.mock_usdc_address,
            agentic_commerce=self.settings.agentic_commerce_address,
            client_wallet=self.settings.client_agent_wallet,
            worker_wallet=self.settings.worker_agent_wallet,
            evaluator_wallet=self.settings.evaluator_agent_wallet,
        )
        self.last_steps = []
        self.last_pacts = []
        return self.state()

    async def run_demo(self) -> dict[str, Any]:
        self.reset()
        tx_hashes: list[str] = []
        steps: list[dict[str, Any]] = []

        # 1. Each money-relevant agent receives a separate scoped CAW pact.
        client_pact = await self.caw.submit_pact(self.client_agent.build_funding_pact(budget=DEMO_BUDGET, total_budget=DEMO_TOTAL_BUDGET))
        worker_pact = await self.caw.submit_pact(self.worker_agent.build_submission_pact())
        evaluator_pact = await self.caw.submit_pact(self.evaluator_agent.build_evaluation_pact())
        self.last_pacts = [client_pact, worker_pact, evaluator_pact]
        steps.append({"agent": "ClientAgent", "title": "Submitted scoped CAW pact", "status": "ok", "details": {"pact_id": client_pact.pact_id}})
        steps.append({"agent": "WorkerAgent", "title": "Submitted delivery CAW pact", "status": "ok", "details": {"pact_id": worker_pact.pact_id}})
        steps.append({"agent": "EvaluatorAgent", "title": "Submitted evaluation CAW pact", "status": "ok", "details": {"pact_id": evaluator_pact.pact_id}})

        # 2. Client approves token spending and creates/funds ERC-8183-style job.
        approve = await self.caw.contract_call(
            CawCall(
                wallet_id=self.settings.client_agent_wallet,
                pact_id=client_pact.pact_id,
                action="contract_call",
                contract=self.settings.mock_usdc_address,
                function_name="approve",
                amount=DEMO_BUDGET,
                details={"spender": self.settings.agentic_commerce_address, "amount": DEMO_BUDGET},
            )
        )
        tx_hashes.append(approve.tx_hash or fake_tx_hash("approve"))
        steps.append({"agent": "ClientAgent", "title": "Approved MockUSDC escrow spend through CAW", "status": "ok", "details": approve.to_dict()})

        description_hash = self._hash("Audit and patch VulnerableVault reentrancy bug")
        expired_at = int(time()) + 24 * 60 * 60
        create = await self.caw.contract_call(
            CawCall(
                wallet_id=self.settings.client_agent_wallet,
                pact_id=client_pact.pact_id,
                action="contract_call",
                contract=self.settings.agentic_commerce_address,
                function_name="createJob",
                amount=0,
                details={"description_hash": description_hash},
            )
        )
        tx_hashes.append(create.tx_hash or fake_tx_hash("createJob"))
        job = self.escrow.create_job(
            client=self.settings.client_agent_wallet,
            provider=self.settings.worker_agent_wallet,
            evaluator=self.settings.evaluator_agent_wallet,
            token=self.settings.mock_usdc_address,
            expired_at=expired_at,
            description_hash=description_hash,
        )
        steps.append({"agent": "ClientAgent", "title": "Created AgenticCommerce job", "status": "ok", "details": {"tx": create.to_dict(), "job": job.to_dict()}})

        set_budget = await self.caw.contract_call(
            CawCall(
                wallet_id=self.settings.client_agent_wallet,
                pact_id=client_pact.pact_id,
                action="contract_call",
                contract=self.settings.agentic_commerce_address,
                function_name="setBudget",
                amount=DEMO_BUDGET,
                details={"job_id": job.job_id, "amount": DEMO_BUDGET},
            )
        )
        tx_hashes.append(set_budget.tx_hash or fake_tx_hash("setBudget"))
        job = self.escrow.set_budget(job.job_id, caller=self.settings.client_agent_wallet, amount=DEMO_BUDGET)
        steps.append({"agent": "ClientAgent", "title": "Set job budget", "status": "ok", "details": {"tx": set_budget.to_dict(), "job": job.to_dict()}})

        fund = await self.caw.contract_call(
            CawCall(
                wallet_id=self.settings.client_agent_wallet,
                pact_id=client_pact.pact_id,
                action="contract_call",
                contract=self.settings.agentic_commerce_address,
                function_name="fund",
                amount=DEMO_BUDGET,
                details={"job_id": job.job_id, "expected_budget": DEMO_BUDGET},
            )
        )
        tx_hashes.append(fund.tx_hash or fake_tx_hash("fund"))
        job = self.escrow.fund(job.job_id, caller=self.settings.client_agent_wallet, expected_budget=DEMO_BUDGET, ledger=self.ledger)
        steps.append({"agent": "ClientAgent", "title": "Funded escrow through CAW", "status": "ok", "details": {"tx": fund.to_dict(), "job": job.to_dict(), "balances": self.ledger.snapshot()}})

        # 3. Worker performs long-horizon audit/fix loop and submits deliverable hash.
        deliverable = self.worker_agent.run(job_id=job.job_id)
        steps.extend(step.to_dict() for step in deliverable.steps)
        submit = await self.caw.contract_call(
            CawCall(
                wallet_id=self.settings.worker_agent_wallet,
                pact_id=worker_pact.pact_id,
                action="contract_call",
                contract=self.settings.agentic_commerce_address,
                function_name="submit",
                amount=0,
                details={"job_id": job.job_id, "deliverable_hash": deliverable.deliverable_hash},
            )
        )
        tx_hashes.append(submit.tx_hash or fake_tx_hash("submit"))
        job = self.escrow.submit(job.job_id, caller=self.settings.worker_agent_wallet, deliverable_hash=deliverable.deliverable_hash)
        steps.append({"agent": "WorkerAgent", "title": "Submitted deliverable hash through CAW", "status": "ok", "details": {"tx": submit.to_dict(), "job": job.to_dict()}})

        # 4. Evaluator verifies deliverable and releases funds.
        evaluation = self.evaluator_agent.run(
            job_id=job.job_id,
            report_path=deliverable.report_path,
            patch_path=deliverable.patch_path,
            deliverable_hash=deliverable.deliverable_hash,
        )
        steps.extend(evaluation.steps)
        if evaluation.decision == "complete":
            complete = await self.caw.contract_call(
                CawCall(
                    wallet_id=self.settings.evaluator_agent_wallet,
                    pact_id=evaluator_pact.pact_id,
                    action="contract_call",
                    contract=self.settings.agentic_commerce_address,
                    function_name="complete",
                    amount=0,
                    details={"job_id": job.job_id, "reason_hash": evaluation.reason_hash},
                )
            )
            tx_hashes.append(complete.tx_hash or fake_tx_hash("complete"))
            job = self.escrow.complete(job.job_id, caller=self.settings.evaluator_agent_wallet, reason_hash=evaluation.reason_hash, ledger=self.ledger)
            steps.append({"agent": "EvaluatorAgent", "title": "Completed job and released payment through CAW", "status": "ok", "details": {"tx": complete.to_dict(), "job": job.to_dict(), "balances": self.ledger.snapshot()}})
        else:
            reject = await self.caw.contract_call(
                CawCall(
                    wallet_id=self.settings.evaluator_agent_wallet,
                    pact_id=evaluator_pact.pact_id,
                    action="contract_call",
                    contract=self.settings.agentic_commerce_address,
                    function_name="reject",
                    amount=0,
                    details={"job_id": job.job_id, "reason_hash": evaluation.reason_hash},
                )
            )
            tx_hashes.append(reject.tx_hash or fake_tx_hash("reject"))
            job = self.escrow.reject(job.job_id, caller=self.settings.evaluator_agent_wallet, reason_hash=evaluation.reason_hash, ledger=self.ledger)
            steps.append({"agent": "EvaluatorAgent", "title": "Rejected job and refunded client through CAW", "status": "rejected", "details": {"tx": reject.to_dict(), "job": job.to_dict()}})

        # 5. Prove CAW boundary: attempt to exceed approved amount.
        denial_payload = None
        try:
            await self.caw.transfer_tokens(
                CawCall(
                    wallet_id=self.settings.client_agent_wallet,
                    pact_id=client_pact.pact_id,
                    action="transfer_tokens",
                    contract=self.settings.mock_usdc_address,
                    function_name="transfer_tokens",
                    amount=20 * MUSDC,
                    details={"purpose": "intentional policy-denial demo"},
                ),
                destination="0x9999999999999999999999999999999999999999",
                token_id="mUSDC",
            )
        except PolicyDenied as exc:
            denial_payload = exc.to_dict()
            steps.append({"agent": "ClientAgent", "title": "CAW denied out-of-policy transfer", "status": "denied", "details": denial_payload})

        logs = await self.caw.list_audit_logs(limit=200)
        self.last_steps = steps
        self.last_evidence = DemoEvidence(
            chain_id=self.settings.chain_id,
            mock_usdc=self.settings.mock_usdc_address,
            agentic_commerce=self.settings.agentic_commerce_address,
            client_wallet=self.settings.client_agent_wallet,
            worker_wallet=self.settings.worker_agent_wallet,
            evaluator_wallet=self.settings.evaluator_agent_wallet,
            job_id=job.job_id,
            tx_hashes=tx_hashes,
            denial=denial_payload,
            deliverable_hash=deliverable.deliverable_hash,
            reason_hash=evaluation.reason_hash,
            report_path=deliverable.report_path,
            patch_path=deliverable.patch_path,
        )
        return self._response(job=job, pacts=self.last_pacts, logs=logs, steps=steps)

    def state(self) -> dict[str, Any]:
        jobs = [job.to_dict() for job in self.escrow.list_jobs()]
        return {
            "balances": self.ledger.snapshot(),
            "jobs": jobs,
            "pacts": [pact.to_dict() for pact in self.last_pacts],
            "agent_steps": self.last_steps,
            "evidence": self.last_evidence.to_dict(),
        }

    async def audit_logs(self) -> list[dict[str, Any]]:
        logs: list[AuditEntry] = await self.caw.list_audit_logs(limit=200)
        return [entry.to_dict() for entry in logs]

    def _response(self, *, job: JobRecord, pacts: list[Pact], logs: list[AuditEntry], steps: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "summary": "PactBounty demo completed: CAW pacts created, escrow funded, worker submitted audit patch, evaluator released payment, and CAW denied an out-of-policy transfer.",
            "pacts": [pact.to_dict() for pact in pacts],
            "job": job.to_dict(),
            "balances": self.ledger.snapshot(),
            "audit_logs": [entry.to_dict() for entry in logs],
            "agent_steps": steps,
            "evidence": self.last_evidence.to_dict(),
        }

    @staticmethod
    def _hash(value: str) -> str:
        return "0x" + hashlib.sha256(value.encode("utf-8")).hexdigest()
