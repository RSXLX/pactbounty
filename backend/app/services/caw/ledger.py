from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Ledger:
    balances: dict[str, int] = field(default_factory=dict)

    def reset(self) -> None:
        self.balances.clear()

    def mint(self, address: str, amount: int) -> None:
        key = self._key(address)
        self.balances[key] = self.balances.get(key, 0) + amount

    def balance(self, address: str) -> int:
        return self.balances.get(self._key(address), 0)

    def transfer(self, src: str, dst: str, amount: int) -> None:
        if amount < 0:
            raise ValueError("amount cannot be negative")
        src_key = self._key(src)
        dst_key = self._key(dst)
        if self.balances.get(src_key, 0) < amount:
            raise ValueError(f"insufficient balance for {src}")
        self.balances[src_key] -= amount
        self.balances[dst_key] = self.balances.get(dst_key, 0) + amount

    def snapshot(self) -> dict[str, int]:
        return dict(sorted(self.balances.items()))

    @staticmethod
    def _key(address: str) -> str:
        return address.lower()
