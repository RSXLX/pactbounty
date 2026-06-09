# Security Boundaries

## Hackathon Boundary

This repo is a hackathon prototype. It is not production audited and must not be used with real user funds.

## Asset Boundary

- Use testnet assets only.
- Use MockUSDC for bounty payment.
- Do not connect wallets holding real assets.
- Keep `PRIVATE_KEY` out of Git and screenshots.

## CAW Policy Boundary

Each agent should have a narrow pact:

### Client Agent

Allowed:

- `MockUSDC.approve(AgenticCommerce, amount)`
- `AgenticCommerce.createJob(...)`
- `AgenticCommerce.setBudget(jobId, amount)`
- `AgenticCommerce.fund(jobId, expectedBudget)`

Limits:

- max single amount: 5 mUSDC for MVP
- total budget: 6 mUSDC
- contract allowlist: MockUSDC + AgenticCommerce
- expiry: 24 hours

### Worker Agent

Allowed:

- `AgenticCommerce.submit(jobId, deliverableHash)`

Limits:

- no token transfer permission required for MVP
- contract allowlist: AgenticCommerce only

### Evaluator Agent

Allowed:

- `AgenticCommerce.complete(jobId, reasonHash)`
- `AgenticCommerce.reject(jobId, reasonHash)`

Limits:

- contract allowlist: AgenticCommerce only
- no arbitrary transfer permission

## LLM Boundary

- GLM-5.1 should never receive private keys.
- GLM-5.1 outputs are treated as proposals.
- Contract-changing actions are gated by tests and evaluator checks.
- Payment actions are gated by CAW pact policies.

## Failure Handling

| Failure | Handling |
|---|---|
| Worker patch fails tests | Evaluator rejects and escrow refunds client. |
| Evaluator cannot verify | Human escalation or reject. |
| CAW denies transaction | Show denial reason; do not retry with broader permissions automatically. |
| Pact expires | Create a new pact after human review. |
| RPC or explorer failure | Use local logs and retry once; do not hide the failure in Demo. |

## What to Say to Judges

"We deliberately show a denial path. The point is not that the Agent is perfectly obedient; the point is that its financial authority is bounded even when it attempts something outside the plan."
