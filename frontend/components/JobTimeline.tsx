import type { AgentStep } from '../lib/api';
import { StatusBadge } from './StatusBadge';

export function JobTimeline({ steps }: { steps: AgentStep[] }) {
  if (!steps?.length) {
    return <p className="muted">No agent execution trace yet. Run the demo to populate the timeline.</p>;
  }
  return (
    <div className="timeline">
      {steps.map((step, idx) => (
        <div className="timeline-item" key={`${step.agent}-${idx}`}>
          <div className="timeline-dot">{idx + 1}</div>
          <div>
            <div className="timeline-title">
              <strong>{step.agent}</strong> · {step.title} <StatusBadge status={step.status} />
            </div>
            <pre>{JSON.stringify(step.details || {}, null, 2)}</pre>
          </div>
        </div>
      ))}
    </div>
  );
}
