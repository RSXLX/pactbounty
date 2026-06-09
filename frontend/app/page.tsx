'use client';

import { useEffect, useMemo, useState } from 'react';
import { AuditLogTable } from '../components/AuditLogTable';
import { BalanceCard } from '../components/BalanceCard';
import { EvidencePanel } from '../components/EvidencePanel';
import { JobTimeline } from '../components/JobTimeline';
import { getState, resetDemo, runDemo, type DemoResponse, type StateResponse } from '../lib/api';

function toDemoLike(state: StateResponse): DemoResponse {
  return {
    summary: 'Ready. Run the demo to execute CAW-gated agent work agreement flow.',
    pacts: state.pacts || [],
    job: state.jobs?.[0],
    balances: state.balances || {},
    audit_logs: [],
    agent_steps: state.agent_steps || [],
    evidence: state.evidence
  } as DemoResponse;
}

function short(value?: string | null) {
  if (!value) return '-';
  return value.length > 18 ? `${value.slice(0, 8)}…${value.slice(-6)}` : value;
}

export default function Home() {
  const [data, setData] = useState<DemoResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    const state = await getState();
    setData(toDemoLike(state));
  }

  async function handleRun() {
    setError(null);
    setLoading(true);
    try {
      const result = await runDemo();
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  async function handleReset() {
    setError(null);
    setLoading(true);
    try {
      const state = await resetDemo();
      setData(toDemoLike(state));
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load().catch((err) => setError(err instanceof Error ? err.message : String(err)));
  }, []);

  const balances = data?.balances || {};
  const evidence = data?.evidence;
  const job = data?.job;

  const balanceCards = useMemo(() => {
    if (!evidence) return [];
    return [
      { title: 'Client Agent', address: evidence.client_wallet, amount: balances[evidence.client_wallet.toLowerCase()] || 0 },
      { title: 'Worker Agent', address: evidence.worker_wallet, amount: balances[evidence.worker_wallet.toLowerCase()] || 0 },
      { title: 'Evaluator Agent', address: evidence.evaluator_wallet, amount: balances[evidence.evaluator_wallet.toLowerCase()] || 0 },
      { title: 'Escrow', address: '0xE5cRow0000000000000000000000000000000000', amount: balances['0xe5crow0000000000000000000000000000000000'] || 0 }
    ];
  }, [balances, evidence]);

  return (
    <main>
      <section className="hero">
        <div>
          <div className="eyebrow">AI × Web3 Agentic Builders Hackathon</div>
          <h1>PactBounty</h1>
          <p>
            CAW-powered agent-to-agent work agreements: Client Agent funds a Web3 audit bounty, Worker Agent patches the contract,
            Evaluator Agent verifies and releases payment, and CAW blocks out-of-policy spending.
          </p>
          <div className="hero-actions">
            <button onClick={handleRun} disabled={loading}>{loading ? 'Running…' : 'Run Full Demo'}</button>
            <button className="secondary" onClick={handleReset} disabled={loading}>Reset</button>
          </div>
          {error && <div className="error">{error}</div>}
        </div>
        <div className="card hero-card">
          <div className="metric">
            <span>Current Job</span>
            <strong>{job?.job_id || '-'}</strong>
          </div>
          <div className="metric">
            <span>Job State</span>
            <strong>{job?.state || 'Ready'}</strong>
          </div>
          <div className="metric">
            <span>Deliverable</span>
            <code>{short(evidence?.deliverable_hash)}</code>
          </div>
        </div>
      </section>

      <section className="grid four">
        {balanceCards.map((card) => (
          <BalanceCard key={card.title} title={card.title} address={card.address} amount={card.amount} />
        ))}
      </section>

      {evidence && (
        <section>
          <EvidencePanel evidence={evidence} pacts={data?.pacts || []} job={job} />
        </section>
      )}

      <section className="grid two">
        <div className="card">
          <h2>Agent Execution Trace</h2>
          <JobTimeline steps={data?.agent_steps || []} />
        </div>
        <div className="card">
          <h2>CAW Audit Logs</h2>
          <AuditLogTable logs={data?.audit_logs || []} />
        </div>
      </section>

      <section className="card">
        <h2>Judge-facing narrative</h2>
        <ol className="story">
          <li>Owner approves scoped CAW pacts for Client, Worker and Evaluator Agents.</li>
          <li>Client Agent approves MockUSDC and funds an ERC-8183-style escrow job.</li>
          <li>Worker Agent performs a long-horizon audit/fix loop and submits the patch hash.</li>
          <li>Evaluator Agent verifies invariants and completes the job, releasing payment.</li>
          <li>Client Agent attempts a bad transfer; CAW denies it and records the policy violation.</li>
        </ol>
      </section>
    </main>
  );
}
