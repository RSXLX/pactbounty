import type { AuditEntry } from '../lib/api';
import { StatusBadge } from './StatusBadge';

function short(value?: string | null) {
  if (!value) return '-';
  return value.length > 16 ? `${value.slice(0, 10)}…${value.slice(-6)}` : value;
}

function fmt(amount: number) {
  return amount ? `${(amount / 1_000_000).toFixed(2)}` : '-';
}

export function AuditLogTable({ logs }: { logs: AuditEntry[] }) {
  if (!logs?.length) return <p className="muted">No CAW audit logs yet.</p>;
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Result</th>
            <th>Action</th>
            <th>Function</th>
            <th>Amount</th>
            <th>Reason</th>
            <th>Tx / Request</th>
          </tr>
        </thead>
        <tbody>
          {logs.map((log) => (
            <tr key={log.id}>
              <td><StatusBadge status={log.result} /></td>
              <td>{log.action}</td>
              <td>{log.function_name || '-'}</td>
              <td>{fmt(log.amount)}</td>
              <td>{log.reason || '-'}</td>
              <td><code>{short(log.tx_hash || log.request_id)}</code></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
