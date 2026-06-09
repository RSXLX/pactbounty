# PactBounty Architecture

## System Overview

```text
User / Judge
   |
   v
Next.js Demo Dashboard
   |
   v
FastAPI Orchestrator
   |----------------------|
   |                      |
Agents                 Adapters
   |                      |
ClientAgent             MockCawClient / RealCawClient
WorkerAgent             Mock ZAI / Real ZAI GLM-5.1
EvaluatorAgent          In-memory escrow / Deployed AgenticCommerce
   |
   v
Solidity Contracts
   |
MockUSDC + AgenticCommerce + VulnerableVault + PatchedVault
```

## Core Runtime Flow

1. ClientAgent builds a CAW pact for `approve`, `createJob`, `setBudget`, `fund`.
2. WorkerAgent builds a CAW pact for `submit`.
3. EvaluatorAgent builds a CAW pact for `complete` / `reject`.
4. CAW validates every call against:
   - wallet identity
   - contract allowlist
   - function allowlist
   - amount ceiling
5. Escrow state machine moves:
   - `Open` → `Funded` → `Submitted` → `Completed`
6. Ledger moves:
   - Client balance decreases by 5 mUSDC
   - Escrow temporarily holds 5 mUSDC
   - Worker receives 5 mUSDC when Evaluator completes
7. CAW denial demo proves that an out-of-policy transfer cannot execute.

## Backend Modules

```text
backend/app/main.py
  FastAPI routes and singleton workflow

backend/app/services/workflow/runner.py
  End-to-end demo orchestration

backend/app/services/caw/
  base.py             shared CAW data models
  mock_client.py      deterministic local CAW simulator
  real_caw_client.py  live Cobo Agentic Wallet SDK adapter
  ledger.py           local mUSDC balance simulator

backend/app/services/escrow/service.py
  In-memory equivalent of AgenticCommerce state machine

backend/app/services/llm/zai_client.py
  Z.AI OpenAI-compatible adapter with mock fallback

backend/app/agents/
  client_agent.py
  worker_agent.py
  evaluator_agent.py
```

## Contract Modules

```text
contracts/src/MockUSDC.sol
  Minimal ERC20-compatible 6-decimal token

contracts/src/AgenticCommerce.sol
  ERC-8183-inspired escrow primitive

contracts/src/VulnerableVault.sol
  Intentional reentrancy target

contracts/src/PatchedVault.sol
  Worker's expected repaired implementation
```

## Why the Mock Layer Exists

For a hackathon, the first enemy is a flaky live demo. Mock mode lets the team develop and record the complete UX before live credentials, faucets, RPC, or wallet approval flows are stable. Real mode is isolated in adapters, so replacing mock behavior does not require rewriting the product.

## What Must Be Real for Final Submission

- At least one CAW pact approval screenshot or log.
- At least one live CAW-funded chain transaction.
- At least one CAW policy denial log.
- Deployed `AgenticCommerce` and `MockUSDC` addresses.
- Job ID and transaction hashes for `fund`, `submit`, and `complete` where possible.
