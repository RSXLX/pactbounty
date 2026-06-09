from __future__ import annotations

from uuid import uuid4

from .base import AuditEntry, CawCall, CawResult, Pact, PactSpec, PolicyDenied, fake_tx_hash, utc_now_iso


class MockCawClient:
    """Deterministic local CAW simulator.

    It is intentionally strict: contract/function allowlists and amount ceilings are enforced
    before the workflow mutates escrow state. This gives a faithful demo of the CAW value
    proposition without requiring live Cobo credentials during development.
    """

    def __init__(self) -> None:
        self.pacts: dict[str, Pact] = {}
        self.audit_logs: list[AuditEntry] = []

    async def submit_pact(self, spec: PactSpec) -> Pact:
        pact_id = f"mock-pact-{uuid4().hex[:8]}"
        pact = Pact(
            pact_id=pact_id,
            wallet_id=spec.wallet_id,
            status="active",
            spec=spec,
            api_key=f"mock-pact-key-{uuid4().hex[:12]}",
        )
        self.pacts[pact_id] = pact
        self.audit_logs.append(
            AuditEntry(
                id=f"audit-{uuid4().hex[:8]}",
                ts=utc_now_iso(),
                wallet_id=spec.wallet_id,
                pact_id=pact_id,
                action="submit_pact",
                contract=None,
                function_name=None,
                amount=0,
                result="allowed",
                reason="mock pact auto-approved for local demo",
                details=spec.to_dict(),
            )
        )
        return pact

    async def get_pact(self, pact_id: str) -> Pact:
        if pact_id not in self.pacts:
            raise KeyError(f"unknown pact {pact_id}")
        return self.pacts[pact_id]

    async def contract_call(self, call: CawCall) -> CawResult:
        return await self._allow_or_deny(call)

    async def transfer_tokens(self, call: CawCall, *, destination: str, token_id: str) -> CawResult:
        call.details = {**call.details, "destination": destination, "token_id": token_id}
        return await self._allow_or_deny(call, is_transfer=True)

    async def list_audit_logs(self, wallet_id: str | None = None, limit: int = 100) -> list[AuditEntry]:
        logs = self.audit_logs
        if wallet_id:
            logs = [entry for entry in logs if entry.wallet_id.lower() == wallet_id.lower()]
        return list(reversed(logs[-limit:]))

    async def _allow_or_deny(self, call: CawCall, *, is_transfer: bool = False) -> CawResult:
        pact = self.pacts.get(call.pact_id)
        if pact is None or pact.status != "active":
            return self._deny(call, "pact is not active", code="inactive_pact")
        if call.wallet_id.lower() != pact.wallet_id.lower():
            return self._deny(call, "wallet does not match pact", code="wallet_mismatch")

        if call.amount > pact.spec.max_single_tx_amount:
            return self._deny(
                call,
                f"amount {call.amount} exceeds max_single_tx_amount {pact.spec.max_single_tx_amount}",
                code="amount_limit_exceeded",
            )

        if call.contract and call.contract.lower() not in [c.lower() for c in pact.spec.allowed_contracts]:
            return self._deny(
                call,
                "contract is outside pact allowlist",
                code="contract_not_allowed",
                details={"contract": call.contract, "allowed_contracts": pact.spec.allowed_contracts},
            )

        function_name = call.function_name or call.action
        if function_name not in pact.spec.allowed_functions:
            return self._deny(
                call,
                "function is outside pact allowlist",
                code="function_not_allowed",
                details={"function_name": function_name, "allowed_functions": pact.spec.allowed_functions},
            )

        request_id = f"req-{uuid4().hex[:10]}"
        tx_hash = fake_tx_hash(request_id)
        result = CawResult(
            id=f"tx-{uuid4().hex[:10]}",
            status="submitted" if not is_transfer else "completed",
            request_id=request_id,
            tx_hash=tx_hash,
            details={"mock": True, **call.details},
        )
        self.audit_logs.append(
            AuditEntry(
                id=f"audit-{uuid4().hex[:8]}",
                ts=utc_now_iso(),
                wallet_id=call.wallet_id,
                pact_id=call.pact_id,
                action=call.action,
                contract=call.contract,
                function_name=call.function_name,
                amount=call.amount,
                result="allowed",
                reason="within pact policy",
                tx_hash=tx_hash,
                request_id=request_id,
                details=call.details,
            )
        )
        return result

    def _deny(self, call: CawCall, reason: str, *, code: str = "policy_denied", details: dict | None = None) -> CawResult:
        entry = AuditEntry(
            id=f"audit-{uuid4().hex[:8]}",
            ts=utc_now_iso(),
            wallet_id=call.wallet_id,
            pact_id=call.pact_id,
            action=call.action,
            contract=call.contract,
            function_name=call.function_name,
            amount=call.amount,
            result="denied",
            reason=reason,
            details=details or call.details,
        )
        self.audit_logs.append(entry)
        raise PolicyDenied(reason, code=code, details=entry.details)
