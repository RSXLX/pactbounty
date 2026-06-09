from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

JobState = Literal["Open", "Funded", "Submitted", "Completed", "Rejected", "Refunded"]
AuditResult = Literal["allowed", "denied", "info"]


class ApiError(BaseModel):
    error: str
    details: dict[str, Any] = Field(default_factory=dict)


class HealthResponse(BaseModel):
    ok: bool
    service: str
    mode: str


class PactSpecModel(BaseModel):
    intent: str
    wallet_id: str
    allowed_contracts: list[str]
    allowed_functions: list[str]
    max_single_tx_amount: int
    total_budget: int
    expires_in_seconds: int = 86400


class PactModel(BaseModel):
    pact_id: str
    wallet_id: str
    status: str
    api_key: str | None = None
    spec: PactSpecModel


class JobModel(BaseModel):
    job_id: int
    client: str
    provider: str
    evaluator: str
    token: str
    budget: int
    escrowed: int
    expired_at: int
    description_hash: str
    deliverable_hash: str | None = None
    reason_hash: str | None = None
    state: str


class AuditEntryModel(BaseModel):
    id: str
    ts: str
    wallet_id: str
    pact_id: str | None = None
    action: str
    contract: str | None = None
    function_name: str | None = None
    amount: int = 0
    result: AuditResult
    reason: str | None = None
    tx_hash: str | None = None
    request_id: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class AgentStepModel(BaseModel):
    agent: str
    title: str
    status: str = "ok"
    details: dict[str, Any] = Field(default_factory=dict)


class DemoRunResponse(BaseModel):
    summary: str
    pacts: list[PactModel]
    job: JobModel
    balances: dict[str, int]
    audit_logs: list[AuditEntryModel]
    agent_steps: list[AgentStepModel]
    evidence: dict[str, Any]
