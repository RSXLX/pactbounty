export const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

export type Job = {
  job_id: number;
  client: string;
  provider: string;
  evaluator: string;
  token: string;
  budget: number;
  escrowed: number;
  expired_at: number;
  description_hash: string;
  deliverable_hash?: string | null;
  reason_hash?: string | null;
  state: string;
};

export type Pact = {
  pact_id: string;
  wallet_id: string;
  status: string;
  api_key?: string | null;
  spec: {
    intent: string;
    wallet_id: string;
    allowed_contracts: string[];
    allowed_functions: string[];
    max_single_tx_amount: number;
    total_budget: number;
    expires_in_seconds: number;
  };
};

export type AuditEntry = {
  id: string;
  ts: string;
  wallet_id: string;
  pact_id?: string | null;
  action: string;
  contract?: string | null;
  function_name?: string | null;
  amount: number;
  result: 'allowed' | 'denied' | 'info';
  reason?: string | null;
  tx_hash?: string | null;
  request_id?: string | null;
  details: Record<string, unknown>;
};

export type AgentStep = {
  agent: string;
  title: string;
  status: string;
  details: Record<string, unknown>;
};

export type Evidence = {
  chain_id: number;
  mock_usdc: string;
  agentic_commerce: string;
  client_wallet: string;
  worker_wallet: string;
  evaluator_wallet: string;
  job_id?: number | null;
  tx_hashes: string[];
  denial?: Record<string, unknown> | null;
  deliverable_hash?: string | null;
  reason_hash?: string | null;
  report_path?: string | null;
  patch_path?: string | null;
};

export type DemoResponse = {
  summary: string;
  pacts: Pact[];
  job: Job;
  balances: Record<string, number>;
  audit_logs: AuditEntry[];
  agent_steps: AgentStep[];
  evidence: Evidence;
};

export type StateResponse = {
  balances: Record<string, number>;
  jobs: Job[];
  pacts: Pact[];
  agent_steps: AgentStep[];
  evidence: Evidence;
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...(init?.headers || {}) },
    cache: 'no-store'
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${body}`);
  }
  return (await res.json()) as T;
}

export function getState() {
  return request<StateResponse>('/state');
}

export function runDemo() {
  return request<DemoResponse>('/demo/run', { method: 'POST' });
}

export function resetDemo() {
  return request<StateResponse>('/demo/reset', { method: 'POST' });
}
