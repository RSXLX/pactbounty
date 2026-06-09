from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from time import time

from app.services.caw.ledger import Ledger

ESCROW_ADDRESS = "0xE5cRow0000000000000000000000000000000000"


class JobState(str, Enum):
    OPEN = "Open"
    FUNDED = "Funded"
    SUBMITTED = "Submitted"
    COMPLETED = "Completed"
    REJECTED = "Rejected"
    REFUNDED = "Refunded"


@dataclass
class JobRecord:
    job_id: int
    client: str
    provider: str
    evaluator: str
    token: str
    budget: int
    escrowed: int
    expired_at: int
    description_hash: str
    deliverable_hash: str | None
    reason_hash: str | None
    state: JobState

    def to_dict(self) -> dict:
        data = asdict(self)
        data["state"] = self.state.value
        return data


class EscrowService:
    """In-memory model of the AgenticCommerce Solidity state machine."""

    def __init__(self) -> None:
        self.next_job_id = 1
        self.jobs: dict[int, JobRecord] = {}

    def reset(self) -> None:
        self.next_job_id = 1
        self.jobs.clear()

    def create_job(self, *, client: str, provider: str, evaluator: str, token: str, expired_at: int, description_hash: str) -> JobRecord:
        if expired_at <= int(time()):
            raise ValueError("expired_at must be in the future")
        job_id = self.next_job_id
        self.next_job_id += 1
        job = JobRecord(
            job_id=job_id,
            client=client,
            provider=provider,
            evaluator=evaluator,
            token=token,
            budget=0,
            escrowed=0,
            expired_at=expired_at,
            description_hash=description_hash,
            deliverable_hash=None,
            reason_hash=None,
            state=JobState.OPEN,
        )
        self.jobs[job_id] = job
        return job

    def set_budget(self, job_id: int, *, caller: str, amount: int) -> JobRecord:
        job = self._job(job_id)
        self._require_state(job, JobState.OPEN)
        if caller.lower() not in {job.client.lower(), job.provider.lower()}:
            raise PermissionError("only client or provider can set budget")
        if amount <= 0:
            raise ValueError("budget must be positive")
        job.budget = amount
        return job

    def fund(self, job_id: int, *, caller: str, expected_budget: int, ledger: Ledger) -> JobRecord:
        job = self._job(job_id)
        self._require_state(job, JobState.OPEN)
        if caller.lower() != job.client.lower():
            raise PermissionError("only client can fund job")
        if job.budget != expected_budget:
            raise ValueError("budget mismatch")
        ledger.transfer(job.client, ESCROW_ADDRESS, job.budget)
        job.escrowed = job.budget
        job.state = JobState.FUNDED
        return job

    def submit(self, job_id: int, *, caller: str, deliverable_hash: str) -> JobRecord:
        job = self._job(job_id)
        self._require_state(job, JobState.FUNDED)
        if caller.lower() != job.provider.lower():
            raise PermissionError("only provider can submit")
        job.deliverable_hash = deliverable_hash
        job.state = JobState.SUBMITTED
        return job

    def complete(self, job_id: int, *, caller: str, reason_hash: str, ledger: Ledger) -> JobRecord:
        job = self._job(job_id)
        self._require_state(job, JobState.SUBMITTED)
        if caller.lower() != job.evaluator.lower():
            raise PermissionError("only evaluator can complete")
        amount = job.escrowed
        ledger.transfer(ESCROW_ADDRESS, job.provider, amount)
        job.escrowed = 0
        job.reason_hash = reason_hash
        job.state = JobState.COMPLETED
        return job

    def reject(self, job_id: int, *, caller: str, reason_hash: str, ledger: Ledger) -> JobRecord:
        job = self._job(job_id)
        if job.state == JobState.OPEN:
            if caller.lower() != job.client.lower():
                raise PermissionError("only client can reject open job")
        elif job.state in {JobState.FUNDED, JobState.SUBMITTED}:
            if caller.lower() != job.evaluator.lower():
                raise PermissionError("only evaluator can reject funded/submitted job")
        else:
            raise ValueError("job already terminal")

        if job.escrowed > 0:
            ledger.transfer(ESCROW_ADDRESS, job.client, job.escrowed)
            job.escrowed = 0
        job.reason_hash = reason_hash
        job.state = JobState.REJECTED
        return job

    def claim_refund(self, job_id: int, *, ledger: Ledger) -> JobRecord:
        job = self._job(job_id)
        if job.state not in {JobState.FUNDED, JobState.SUBMITTED}:
            raise ValueError("only funded/submitted jobs can be refunded")
        if int(time()) < job.expired_at:
            raise ValueError("job is not expired")
        ledger.transfer(ESCROW_ADDRESS, job.client, job.escrowed)
        job.escrowed = 0
        job.state = JobState.REFUNDED
        return job

    def get_job(self, job_id: int) -> JobRecord:
        return self._job(job_id)

    def list_jobs(self) -> list[JobRecord]:
        return [self.jobs[k] for k in sorted(self.jobs.keys())]

    def _job(self, job_id: int) -> JobRecord:
        if job_id not in self.jobs:
            raise KeyError(f"unknown job {job_id}")
        return self.jobs[job_id]

    @staticmethod
    def _require_state(job: JobRecord, expected: JobState) -> None:
        if job.state != expected:
            raise ValueError(f"invalid job state: expected {expected.value}, got {job.state.value}")
