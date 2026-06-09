from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from uuid import uuid4

from app.config import DELIVERABLES_DIR
from app.services.caw import PactSpec


@dataclass
class EvaluationResult:
    decision: str
    score: int
    reason_hash: str
    report_path: str
    details: dict
    steps: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class EvaluatorAgent:
    wallet: str
    escrow_contract: str

    def build_evaluation_pact(self) -> PactSpec:
        return PactSpec(
            intent="PactBounty Evaluator Agent may complete or reject submitted jobs after verification.",
            wallet_id=self.wallet,
            allowed_contracts=[self.escrow_contract],
            allowed_functions=["complete", "reject"],
            max_single_tx_amount=0,
            total_budget=0,
        )

    def run(self, *, job_id: int, report_path: str, patch_path: str, deliverable_hash: str) -> EvaluationResult:
        report = Path(report_path).read_text(encoding="utf-8")
        patch = Path(patch_path).read_text(encoding="utf-8")
        checks = {
            "has_reentrancy_finding": "Reentrancy" in report or "reentrancy" in report,
            "zeros_balance_before_call": "balances[msg.sender] = 0" in patch and patch.find("balances[msg.sender] = 0") < patch.find("call{value: amount}"),
            "has_guard": "nonReentrant" in patch,
            "hash_prefix_ok": deliverable_hash.startswith("0x") and len(deliverable_hash) == 66,
        }
        passed = all(checks.values())
        score = 92 if passed else 40
        decision = "complete" if passed else "reject"
        reason_payload = {
            "job_id": job_id,
            "decision": decision,
            "score": score,
            "checks": checks,
            "deliverable_hash": deliverable_hash,
        }
        reason_hash = "0x" + hashlib.sha256(json.dumps(reason_payload, sort_keys=True).encode("utf-8")).hexdigest()

        run_dir = DELIVERABLES_DIR / f"evaluation-{job_id}-{uuid4().hex[:8]}"
        run_dir.mkdir(parents=True, exist_ok=True)
        out_path = run_dir / "evaluation.json"
        out_path.write_text(json.dumps(reason_payload, ensure_ascii=False, indent=2), encoding="utf-8")

        steps = [
            {"agent": "EvaluatorAgent", "title": "Loaded Worker deliverable", "status": "ok", "details": {"report_path": report_path, "patch_path": patch_path}},
            {"agent": "EvaluatorAgent", "title": "Checked patch invariants", "status": "ok" if passed else "failed", "details": checks},
            {"agent": "EvaluatorAgent", "title": "Produced structured decision", "status": decision, "details": {"score": score, "reason_hash": reason_hash}},
        ]
        return EvaluationResult(decision=decision, score=score, reason_hash=reason_hash, report_path=str(out_path), details=reason_payload, steps=steps)
