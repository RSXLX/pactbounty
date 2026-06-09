# Real CAW and GLM-5.1 Integration Guide

## 1. CAW Setup

Follow the Cobo Agentic Wallet onboarding flow:

```bash
curl -fsSL https://raw.githubusercontent.com/CoboGlobal/cobo-agentic-wallet/master/install.sh | bash
export PATH="$HOME/.cobo-agentic-wallet/bin:$PATH"
caw --version
caw onboard --wait --invitation-code <invitation-code>
caw wallet pair --code-only
caw wallet pair-status
caw wallet current --show-api-key
```

Set env vars:

```bash
CAW_MODE=real
AGENT_WALLET_API_URL=https://api.agenticwallet.cobo.com
AGENT_WALLET_API_KEY=...
AGENT_WALLET_WALLET_ID=...
CAW_CHAIN_ID=SETH
CAW_TOKEN_ID=SETH
```

## 2. Install SDK

```bash
cd backend
pip install cobo-agentic-wallet
```

The live integration is centralized in:

```text
backend/app/services/caw/real_caw_client.py
```

Start by making only one real operation work:

1. `submit_pact`
2. wait until owner approves
3. `transfer_tokens` small allowed amount
4. attempt denied amount
5. `list_audit_logs`

Only after that should you wire `contract_call` into the escrow flow.

## 3. Contract Call ABI Mapping

For real chain execution, each action needs ABI + args:

### MockUSDC.approve

```json
{
  "contract": "MOCK_USDC_ADDRESS",
  "function_name": "approve",
  "args": ["AGENTIC_COMMERCE_ADDRESS", "5000000"]
}
```

### AgenticCommerce.createJob

```json
{
  "contract": "AGENTIC_COMMERCE_ADDRESS",
  "function_name": "createJob",
  "args": ["WORKER_AGENT_WALLET", "EVALUATOR_AGENT_WALLET", "MOCK_USDC_ADDRESS", "EXPIRED_AT", "DESCRIPTION_HASH"]
}
```

### AgenticCommerce.setBudget

```json
{
  "function_name": "setBudget",
  "args": ["JOB_ID", "5000000"]
}
```

### AgenticCommerce.fund

```json
{
  "function_name": "fund",
  "args": ["JOB_ID", "5000000"]
}
```

### AgenticCommerce.submit

```json
{
  "function_name": "submit",
  "args": ["JOB_ID", "DELIVERABLE_HASH"]
}
```

### AgenticCommerce.complete

```json
{
  "function_name": "complete",
  "args": ["JOB_ID", "REASON_HASH"]
}
```

## 4. GLM-5.1 Setup

Set:

```bash
LLM_MODE=real
ZAI_API_KEY=...
ZAI_BASE_URL=https://api.z.ai/api/paas/v4/
ZAI_MODEL=glm-5.1
```

The adapter is:

```text
backend/app/services/llm/zai_client.py
```

For demo stability, keep a deterministic fallback. If GLM fails or returns malformed JSON, the demo should continue in mock mode but mark that fallback in trace.

## 5. Evidence Collection

For final submission, capture:

- pact approval screenshot
- CAW allowed transfer / contract call log
- CAW denied transfer log
- explorer tx for fund
- explorer tx for complete
- final dashboard screenshot
- generated audit report and patch hash
