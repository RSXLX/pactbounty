# 3–5 Minute Demo Script

## 0:00–0:25 — Hook

"Today AI agents can write code, but they still cannot safely hire another agent, escrow funds, verify work, and pay. PactBounty solves that with Cobo Agentic Wallet and an ERC-8183-style work agreement."

## 0:25–0:55 — Product Setup

Show the dashboard.

Say:

"We have three agents: Client, Worker, and Evaluator. The task is to audit and patch a vulnerable Solidity vault. The bounty is 5 mUSDC. Every money-related action is gated by a CAW pact."

## 0:55–1:35 — CAW Pact Boundary

Click **Run Full Demo**.

Point out:

- ClientAgent pact: `approve`, `createJob`, `setBudget`, `fund`.
- WorkerAgent pact: `submit`.
- EvaluatorAgent pact: `complete`, `reject`.

Say:

"The agent does not hold a private key. It receives scoped authority: contract allowlist, function allowlist, amount limit, and expiration."

## 1:35–2:20 — Escrow Funding

Show state transition to `Funded` and balance movement.

Say:

"Client Agent approves MockUSDC and funds the AgenticCommerce escrow. The funds leave the Client Agent and sit in escrow, not with the Worker."

## 2:20–3:10 — Worker Agent Long-Horizon Task

Show Agent Execution Trace.

Say:

"Worker Agent reads the vulnerable contract, identifies reentrancy, creates a patch, verifies the invariant, writes an audit report, and submits a deliverable hash. In real mode this step is driven by GLM-5.1."

## 3:10–3:50 — Evaluator Releases Payment

Show `Submitted` → `Completed`, Worker balance +5 mUSDC.

Say:

"Evaluator Agent verifies that balance is zeroed before the external call and that a nonReentrant guard exists. It then calls complete through CAW, releasing payment to the Worker Agent."

## 3:50–4:35 — CAW Denial Proof

Show denied audit log.

Say:

"Finally the Client Agent tries to transfer 20 mUSDC to an unplanned address. This exceeds the approved CAW pact, so CAW denies it. This is the key: safety is enforced by wallet infrastructure, not by trusting the prompt."

## 4:35–5:00 — Close

"PactBounty is a minimal Agentic Economy: agents can hire, work, verify, get paid, and fail safely. The same primitive can power audit bounties, research jobs, data procurement, API payments, and DAO operations."
