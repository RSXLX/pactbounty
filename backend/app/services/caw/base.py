from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Protocol
from uuid import uuid4


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def fake_tx_hash(seed: str | None = None) -> str:
    raw = (seed or str(uuid4())).encode("utf-8").hex()
    return "0x" + (raw + "0" * 64)[:64]


@dataclass
class PactSpec:
    intent: str
    wallet_id: str
    allowed_contracts: list[str]
    allowed_functions: list[str]
    max_single_tx_amount: int
    total_budget: int
    expires_in_seconds: int = 86_400

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Pact:
    pact_id: str
    wallet_id: str
    status: str
    spec: PactSpec
    api_key: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "pact_id": self.pact_id,
            "wallet_id": self.wallet_id,
            "status": self.status,
            "api_key": self.api_key,
            "spec": self.spec.to_dict(),
        }


@dataclass
class CawCall:
    wallet_id: str
    pact_id: str
    action: str
    contract: str | None = None
    function_name: str | None = None
    amount: int = 0
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class CawResult:
    id: str
    status: str
    request_id: str
    tx_hash: str | None
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AuditEntry:
    id: str
    ts: str
    wallet_id: str
    pact_id: str | None
    action: str
    contract: str | None
    function_name: str | None
    amount: int
    result: str
    reason: str | None = None
    tx_hash: str | None = None
    request_id: str | None = None
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class PolicyDenied(Exception):
    def __init__(self, reason: str, *, code: str = "policy_denied", details: dict[str, Any] | None = None, suggestion: str | None = None):
        super().__init__(reason)
        self.reason = reason
        self.code = code
        self.details = details or {}
        self.suggestion = suggestion or "Reduce the requested amount or request a new pact with a narrower approved policy."

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "reason": self.reason,
            "details": self.details,
            "suggestion": self.suggestion,
        }


class CawClient(Protocol):
    async def submit_pact(self, spec: PactSpec) -> Pact: ...
    async def get_pact(self, pact_id: str) -> Pact: ...
    async def contract_call(self, call: CawCall) -> CawResult: ...
    async def transfer_tokens(self, call: CawCall, *, destination: str, token_id: str) -> CawResult: ...
    async def list_audit_logs(self, wallet_id: str | None = None, limit: int = 100) -> list[AuditEntry]: ...
