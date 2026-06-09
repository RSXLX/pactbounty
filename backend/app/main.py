from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.models import DemoRunResponse, HealthResponse
from app.services.workflow import DemoWorkflow

settings = get_settings()
workflow = DemoWorkflow(settings)
workflow.reset()

app = FastAPI(
    title="PactBounty API",
    version="0.1.0",
    description="Backend orchestration for CAW-powered agent-to-agent Web3 audit bounty demo.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(ok=True, service="pactbounty-api", mode=f"caw={settings.caw_mode},llm={settings.llm_mode}")


@app.get("/state")
async def state() -> dict:
    return workflow.state()


@app.post("/demo/reset")
async def reset_demo() -> dict:
    return workflow.reset()


@app.post("/demo/run", response_model=DemoRunResponse)
async def run_demo() -> dict:
    try:
        return await workflow.run_demo()
    except Exception as exc:  # Keep API errors readable during live demo.
        raise HTTPException(status_code=500, detail={"error": str(exc), "type": exc.__class__.__name__}) from exc


@app.get("/jobs")
async def list_jobs() -> dict:
    return {"items": [job.to_dict() for job in workflow.escrow.list_jobs()]}


@app.get("/jobs/{job_id}")
async def get_job(job_id: int) -> dict:
    try:
        return workflow.escrow.get_job(job_id).to_dict()
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/audit-logs")
async def audit_logs() -> dict:
    return {"items": await workflow.audit_logs()}


@app.get("/evidence")
async def evidence() -> dict:
    return workflow.last_evidence.to_dict()
