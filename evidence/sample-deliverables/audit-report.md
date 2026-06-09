# PactBounty Audit Report

## Job
- Job ID: 1
- Target: `contracts/src/VulnerableVault.sol`
- Decision requested: fix high-risk asset-draining vulnerability and provide patch hash.

## Finding
- Severity: High
- Vulnerability: Reentrancy in withdraw(): ETH is sent before user balance is zeroed.

## Reasoning
The contract performs an untrusted external call to msg.sender before updating internal accounting. A malicious receiver can re-enter withdraw() and drain funds.

## Patch
Moved state update before external call and added nonReentrant guard.

## Verification
- Static pattern check: external call before balance update removed.
- Regression test plan: attacker can no longer re-enter withdraw before balance is zeroed.
- Demo mode result: PASS.

## Reviewer Notes
This deliverable is intentionally narrow for a hackathon demo. Production use requires full testnet deployment, Foundry test execution, Slither/Medusa/Echidna where appropriate, and manual human escalation for critical value contracts.
