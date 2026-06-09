from __future__ import annotations

import asyncio
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from app.config import get_settings  # noqa: E402
from app.services.workflow import DemoWorkflow  # noqa: E402


async def main() -> None:
    workflow = DemoWorkflow(get_settings())
    result = await workflow.run_demo()
    evidence_dir = ROOT / "evidence"
    evidence_dir.mkdir(exist_ok=True)
    (evidence_dir / "last-demo-run.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    (evidence_dir / "txs.json").write_text(json.dumps(result["evidence"], ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {evidence_dir / 'last-demo-run.json'}")
    print(f"Wrote {evidence_dir / 'txs.json'}")


if __name__ == "__main__":
    asyncio.run(main())
