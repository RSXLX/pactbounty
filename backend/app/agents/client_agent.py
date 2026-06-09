from __future__ import annotations

from dataclasses import dataclass

from app.services.caw import PactSpec


@dataclass
class ClientAgent:
    wallet: str
    mock_usdc: str
    escrow_contract: str

    def build_funding_pact(self, *, budget: int, total_budget: int) -> PactSpec:
        return PactSpec(
            intent=(
                "PactBounty Client Agent may approve MockUSDC, create an AgenticCommerce job, "
                "set its budget, and fund escrow within the approved demo budget."
            ),
            wallet_id=self.wallet,
            allowed_contracts=[self.mock_usdc, self.escrow_contract],
            allowed_functions=["approve", "createJob", "setBudget", "fund", "transfer_tokens"],
            max_single_tx_amount=budget,
            total_budget=total_budget,
        )
