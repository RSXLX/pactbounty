from __future__ import annotations

import asyncio
import json

from app.config import get_settings
from app.services.workflow import DemoWorkflow


async def main() -> None:
    workflow = DemoWorkflow(get_settings())
    result = await workflow.run_demo()
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
