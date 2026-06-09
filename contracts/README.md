# Contracts

This folder contains the Solidity side of PactBounty.

## Contracts

- `MockUSDC.sol`: 6-decimal ERC20-like token for local/testnet payment demos.
- `AgenticCommerce.sol`: ERC-8183-inspired job escrow: create -> budget -> fund -> submit -> complete/reject/refund.
- `VulnerableVault.sol`: intentionally vulnerable audit target.
- `PatchedVault.sol`: expected safe output for the Worker Agent.

## Install Foundry dependencies

```bash
cd contracts
forge install foundry-rs/forge-std --no-commit
forge build
forge test
```

## Deploy to testnet

```bash
cp ../.env.example ../.env
# Fill RPC_URL, PRIVATE_KEY, CLIENT_AGENT_WALLET, WORKER_AGENT_WALLET
source ../.env
forge script script/Deploy.s.sol:Deploy --rpc-url $RPC_URL --broadcast --verify
```

After deployment, copy the addresses to `.env`:

```bash
MOCK_USDC_ADDRESS=0x...
AGENTIC_COMMERCE_ADDRESS=0x...
```
