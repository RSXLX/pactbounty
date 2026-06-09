import type { Evidence, Pact, Job } from '../lib/api';
import { StatusBadge } from './StatusBadge';

function short(value?: string | null) {
  if (!value) return '-';
  return value.length > 22 ? `${value.slice(0, 12)}…${value.slice(-8)}` : value;
}

export function EvidencePanel({ evidence, pacts, job }: { evidence: Evidence; pacts: Pact[]; job?: Job }) {
  return (
    <div className="card evidence">
      <h2>Demo Evidence</h2>
      <div className="evidence-grid">
        <div><span>Chain</span><strong>{evidence.chain_id}</strong></div>
        <div><span>Job</span><strong>{evidence.job_id || job?.job_id || '-'}</strong></div>
        <div><span>State</span><strong>{job?.state ? <StatusBadge status={job.state} /> : '-'}</strong></div>
        <div><span>Deliverable</span><code>{short(evidence.deliverable_hash)}</code></div>
        <div><span>Reason</span><code>{short(evidence.reason_hash)}</code></div>
        <div><span>MockUSDC</span><code>{short(evidence.mock_usdc)}</code></div>
        <div><span>Escrow</span><code>{short(evidence.agentic_commerce)}</code></div>
        <div><span>Pacts</span><strong>{pacts.length}</strong></div>
      </div>
      <h3>Transaction Hashes</h3>
      <div className="hash-list">
        {(evidence.tx_hashes || []).map((tx) => <code key={tx}>{short(tx)}</code>)}
        {!evidence.tx_hashes?.length && <span className="muted">Run demo to generate mock/testnet hashes.</span>}
      </div>
      {evidence.denial && (
        <div className="denial-box">
          <strong>CAW denial proof</strong>
          <pre>{JSON.stringify(evidence.denial, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}
