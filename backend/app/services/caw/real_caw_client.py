from __future__ import annotations

import asyncio
from typing import Any

from app.config import Settings

from .base import AuditEntry, CawCall, CawResult, Pact, PactSpec, PolicyDenied


class RealCawClient:
    """Thin adapter around Cobo Agentic Wallet Python SDK.

    The official SDK exposes WalletAPIClient for pact, transaction and audit operations.
    This adapter is intentionally centralized so the rest of the project never touches raw
    wallet APIs or private keys. Contract-call argument shapes can be adjusted here if the
    SDK version used by your team changes.
    """

    def __init__(self, settings: Settings) -> None:
        if not settings.agent_wallet_api_key or not settings.agent_wallet_wallet_id:
            raise RuntimeError("AGENT_WALLET_API_KEY and AGENT_WALLET_WALLET_ID are required when CAW_MODE=real")
        try:
            from cobo_agentic_wallet.client import WalletAPIClient  # type: ignore
            from cobo_agentic_wallet.errors import PolicyDeniedError  # type: ignore
        except Exception as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("Install cobo-agentic-wallet to use CAW_MODE=real") from exc

        self.settings = settings
        self._WalletAPIClient = WalletAPIClient
        self._PolicyDeniedError = PolicyDeniedError
        self.owner_client = WalletAPIClient(base_url=settings.agent_wallet_api_url, api_key=settings.agent_wallet_api_key)
        self.pact_clients: dict[str, Any] = {}
        self.pacts: dict[str, Pact] = {}

    async def submit_pact(self, spec: PactSpec) -> Pact:
        response = await self.owner_client.submit_pact(
            wallet_id=self.settings.agent_wallet_wallet_id,
            intent=spec.intent,
            spec={
                "policies": [
                    {
                        "name": "pactbounty-contract-policy",
                        "type": "contract_call",
                        "rules": {
                            "effect": "allow",
                            "when": {
                                "chain_in": [self.settings.caw_chain_id],
                                "contract_in": spec.allowed_contracts,
                                "function_in": spec.allowed_functions,
                            },
                            "deny_if": {"amount_gt": str(spec.max_single_tx_amount)},
                        },
                    }
                ],
                "completion_conditions": [{"type": "time_elapsed", "threshold": str(spec.expires_in_seconds)}],
                "metadata": spec.to_dict(),
            },
        )
        pact_id = response["pact_id"]
        pact = Pact(pact_id=pact_id, wallet_id=spec.wallet_id, status=response.get("status", "pending"), spec=spec, api_key=None)
        self.pacts[pact_id] = pact
        return await self.wait_for_pact_active(pact_id)

    async def wait_for_pact_active(self, pact_id: str, timeout_seconds: int = 600) -> Pact:
        started = asyncio.get_event_loop().time()
        while True:
            raw = await self.owner_client.get_pact(pact_id)
            status = raw.get("status", "")
            if status == "active":
                spec = self.pacts[pact_id].spec
                api_key = raw.get("api_key")
                pact = Pact(pact_id=pact_id, wallet_id=spec.wallet_id, status="active", spec=spec, api_key=api_key)
                self.pacts[pact_id] = pact
                if api_key:
                    self.pact_clients[pact_id] = self._WalletAPIClient(base_url=self.settings.agent_wallet_api_url, api_key=api_key)
                return pact
            if status in {"rejected", "expired", "revoked", "completed"}:
                raise RuntimeError(f"Pact reached terminal status before use: {status}")
            if asyncio.get_event_loop().time() - started > timeout_seconds:
                raise TimeoutError("Timed out waiting for owner to approve CAW pact")
            await asyncio.sleep(5)

    async def get_pact(self, pact_id: str) -> Pact:
        if pact_id not in self.pacts:
            raw = await self.owner_client.get_pact(pact_id)
            raise KeyError(f"pact {pact_id} found in CAW but not in local spec cache: {raw}")
        return self.pacts[pact_id]

    async def contract_call(self, call: CawCall) -> CawResult:
        client = self._pact_client(call.pact_id)
        try:
            # SDK argument names may evolve. Keep all live integration edits here.
            raw = await client.contract_call(
                wallet_id=self.settings.agent_wallet_wallet_id,
                chain_id=self.settings.caw_chain_id,
                contract_address=call.contract,
                function_name=call.function_name,
                args=call.details.get("args", []),
                value=call.details.get("value", "0"),
                abi=call.details.get("abi"),
            )
        except self._PolicyDeniedError as exc:  # type: ignore[misc]
            denial = getattr(exc, "denial", None)
            reason = getattr(denial, "reason", str(exc))
            details = getattr(denial, "details", {}) or {}
            raise PolicyDenied(reason, details=details) from exc

        return CawResult(
            id=str(raw.get("id", "")),
            status=str(raw.get("status", "submitted")),
            request_id=str(raw.get("request_id", "")),
            tx_hash=raw.get("transaction_hash"),
            details=raw,
        )

    async def transfer_tokens(self, call: CawCall, *, destination: str, token_id: str) -> CawResult:
        client = self._pact_client(call.pact_id)
        try:
            raw = await client.transfer_tokens(
                self.settings.agent_wallet_wallet_id,
                chain_id=self.settings.caw_chain_id,
                dst_addr=destination,
                token_id=token_id,
                amount=str(call.amount),
            )
        except self._PolicyDeniedError as exc:  # type: ignore[misc]
            denial = getattr(exc, "denial", None)
            reason = getattr(denial, "reason", str(exc))
            details = getattr(denial, "details", {}) or {}
            raise PolicyDenied(reason, details=details) from exc
        return CawResult(
            id=str(raw.get("id", "")),
            status=str(raw.get("status", "submitted")),
            request_id=str(raw.get("request_id", "")),
            tx_hash=raw.get("transaction_hash"),
            details=raw,
        )

    async def list_audit_logs(self, wallet_id: str | None = None, limit: int = 100) -> list[AuditEntry]:
        raw = await self.owner_client.list_audit_logs(wallet_id=self.settings.agent_wallet_wallet_id, limit=limit)
        entries = raw.get("items", []) if isinstance(raw, dict) else []
        normalized: list[AuditEntry] = []
        for item in entries:
            normalized.append(
                AuditEntry(
                    id=str(item.get("id", "")),
                    ts=str(item.get("created_at", "")),
                    wallet_id=str(item.get("wallet_id", wallet_id or self.settings.agent_wallet_wallet_id)),
                    pact_id=item.get("pact_id"),
                    action=str(item.get("action", item.get("type", "unknown"))),
                    contract=item.get("contract"),
                    function_name=item.get("function_name"),
                    amount=int(item.get("amount", 0) or 0),
                    result=str(item.get("result", "info")),
                    reason=item.get("reason"),
                    tx_hash=item.get("transaction_hash"),
                    request_id=item.get("request_id"),
                    details=item,
                )
            )
        return normalized

    async def close(self) -> None:
        await self.owner_client.close()
        for client in self.pact_clients.values():
            await client.close()

    def _pact_client(self, pact_id: str):
        if pact_id not in self.pact_clients:
            raise RuntimeError("pact is not active or pact-scoped API key is unavailable")
        return self.pact_clients[pact_id]
