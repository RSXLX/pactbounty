# Backend

FastAPI backend for the PactBounty demo. It orchestrates three agents:

- ClientAgent: submits a scoped CAW pact and funds an ERC-8183-style escrow job.
- WorkerAgent: audits and patches the vulnerable Solidity contract, then submits a deliverable hash.
- EvaluatorAgent: verifies the deliverable and releases or rejects payment.

## Local mock mode

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m app.scripts.run_demo
uvicorn app.main:app --reload --port 8000
```

Mock mode proves the full product flow without live wallet credentials:

1. CAW pact auto-approved.
2. MockUSDC approved and escrow funded.
3. Worker generates audit report and patch.
4. Evaluator completes job and releases payment.
5. Out-of-policy transfer is denied and logged.

## Switch to real CAW

1. Install and pair Cobo Agentic Wallet.
2. Set `CAW_MODE=real` and fill `AGENT_WALLET_API_URL`, `AGENT_WALLET_API_KEY`, `AGENT_WALLET_WALLET_ID`.
3. Deploy contracts and fill `MOCK_USDC_ADDRESS`, `AGENTIC_COMMERCE_ADDRESS`.
4. Review `app/services/caw/real_caw_client.py` for the exact SDK version's `contract_call` argument names.

## Switch to real GLM-5.1

Set:

```bash
LLM_MODE=real
ZAI_API_KEY=...
ZAI_BASE_URL=https://api.z.ai/api/paas/v4/
ZAI_MODEL=glm-5.1
```
