from __future__ import annotations

import asyncio

from app.config import get_settings
from app.services.workflow import DemoWorkflow, MUSDC


def test_mock_demo_happy_path() -> None:
    workflow = DemoWorkflow(get_settings())
    result = asyncio.run(workflow.run_demo())

    assert result["job"]["state"] == "Completed"
    assert result["job"]["budget"] == 5 * MUSDC
    assert result["balances"][get_settings().worker_agent_wallet.lower()] == 5 * MUSDC
    assert result["evidence"]["denial"]["code"] == "amount_limit_exceeded"
    assert any(step["status"] == "denied" for step in result["agent_steps"])
