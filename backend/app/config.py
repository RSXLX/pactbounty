from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover - dotenv is optional at import time
    load_dotenv = None

APP_DIR = Path(__file__).resolve().parent
BACKEND_DIR = APP_DIR.parent
PROJECT_DIR = BACKEND_DIR.parent
CONTRACTS_DIR = PROJECT_DIR / "contracts"
STORAGE_DIR = BACKEND_DIR / "storage"
DELIVERABLES_DIR = STORAGE_DIR / "deliverables"


def _load_env() -> None:
    if load_dotenv is not None:
        # Load project root .env if present, otherwise no-op.
        load_dotenv(PROJECT_DIR / ".env")


@dataclass(frozen=True)
class Settings:
    app_env: str = "local"
    caw_mode: str = "mock"
    llm_mode: str = "mock"
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    cors_origins: tuple[str, ...] = ("http://localhost:3000", "http://127.0.0.1:3000")

    agent_wallet_api_url: str = "https://api.agenticwallet.cobo.com"
    agent_wallet_api_key: str = ""
    agent_wallet_wallet_id: str = ""
    caw_chain_id: str = "SETH"
    caw_token_id: str = "SETH"
    caw_agent_address: str = ""

    zai_api_key: str = ""
    zai_base_url: str = "https://api.z.ai/api/paas/v4/"
    zai_model: str = "glm-5.1"

    chain_id: int = 11155111
    mock_usdc_address: str = "0x0000000000000000000000000000000000001000"
    agentic_commerce_address: str = "0x0000000000000000000000000000000000002000"
    client_agent_wallet: str = "0x1111111111111111111111111111111111111111"
    worker_agent_wallet: str = "0x2222222222222222222222222222222222222222"
    evaluator_agent_wallet: str = "0x3333333333333333333333333333333333333333"

    @property
    def is_mock(self) -> bool:
        return self.caw_mode.lower() == "mock"


def _getenv(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    _load_env()
    cors_raw = _getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
    origins = tuple(part.strip() for part in cors_raw.split(",") if part.strip())

    return Settings(
        app_env=_getenv("APP_ENV", "local"),
        caw_mode=_getenv("CAW_MODE", "mock"),
        llm_mode=_getenv("LLM_MODE", "mock"),
        backend_host=_getenv("BACKEND_HOST", "0.0.0.0"),
        backend_port=int(_getenv("BACKEND_PORT", "8000")),
        cors_origins=origins,
        agent_wallet_api_url=_getenv("AGENT_WALLET_API_URL", "https://api.agenticwallet.cobo.com"),
        agent_wallet_api_key=_getenv("AGENT_WALLET_API_KEY", ""),
        agent_wallet_wallet_id=_getenv("AGENT_WALLET_WALLET_ID", ""),
        caw_chain_id=_getenv("CAW_CHAIN_ID", "SETH"),
        caw_token_id=_getenv("CAW_TOKEN_ID", "SETH"),
        caw_agent_address=_getenv("CAW_AGENT_ADDRESS", ""),
        zai_api_key=_getenv("ZAI_API_KEY", ""),
        zai_base_url=_getenv("ZAI_BASE_URL", "https://api.z.ai/api/paas/v4/"),
        zai_model=_getenv("ZAI_MODEL", "glm-5.1"),
        chain_id=int(_getenv("CHAIN_ID", "11155111")),
        mock_usdc_address=_getenv("MOCK_USDC_ADDRESS", "0x0000000000000000000000000000000000001000"),
        agentic_commerce_address=_getenv("AGENTIC_COMMERCE_ADDRESS", "0x0000000000000000000000000000000000002000"),
        client_agent_wallet=_getenv("CLIENT_AGENT_WALLET", "0x1111111111111111111111111111111111111111"),
        worker_agent_wallet=_getenv("WORKER_AGENT_WALLET", "0x2222222222222222222222222222222222222222"),
        evaluator_agent_wallet=_getenv("EVALUATOR_AGENT_WALLET", "0x3333333333333333333333333333333333333333"),
    )
