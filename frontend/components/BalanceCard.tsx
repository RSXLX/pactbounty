function fmt(amount: number) {
  return `${(amount / 1_000_000).toFixed(2)} mUSDC`;
}

function short(address: string) {
  if (!address) return '-';
  return `${address.slice(0, 6)}…${address.slice(-4)}`;
}

export function BalanceCard({ title, address, amount }: { title: string; address: string; amount: number }) {
  return (
    <div className="card balance-card">
      <div className="muted">{title}</div>
      <div className="balance-amount">{fmt(amount || 0)}</div>
      <code>{short(address)}</code>
    </div>
  );
}
