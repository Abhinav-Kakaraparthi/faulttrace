import type { ServerState } from './api';
import type { Mutate } from './workspace';

const phases: Record<string, string> = {
  idle: 'Ready to start', starting: 'Starting the investigation', planning: 'Choosing the next observation',
  awaiting_field_evidence: 'Waiting for Operator to return field evidence',
  awaiting_photo_analysis: 'Photograph stored. Operator can explicitly request image analysis.',
  analyzing_evidence: 'Analyzing submitted evidence', awaiting_independent_review: 'Waiting for an independent human review',
  awaiting_approval: 'Evidence is ready. Commander must approve the simulated correction.',
  awaiting_operator_action: 'Approved. Waiting for Operator to complete the simulated assignment.',
  verifying_recovery: 'Collecting independent post-action measurements', complete: 'Simulated recovery verified',
  escalated: 'Human investigation required', paused: 'Guided investigation paused',
};
export function GuidedInvestigation({state, mutate, disabled}: {state: ServerState; mutate: Mutate; disabled: boolean}) {
  const current = state.continuation;
  if (!current || state.journey?.evidence_mode !== 'task-evidence') return null;
  const active = !!current.enabled;
  return <section className="section-surface guided-investigation" aria-label="Guided investigation">
    <span className="eyebrow">PERSISTENT INVESTIGATION</span><h2 aria-live="polite">{phases[current.phase] ?? 'Review investigation state'}</h2>
    <p>{active ? 'The investigation resumes on the server when field evidence arrives. Approval and equipment acknowledgment remain human decisions.'
      : 'Start a bounded investigation that chooses the next observation after each field response and starts verification after the approved simulated action.'}</p>
    {current.error && <p role="status">Stopped: {current.error.replaceAll('_', ' ')}. Saved evidence and accounting are retained.</p>}
    <button className={`button ${active ? 'secondary' : 'primary'}`} disabled={disabled || (!active && (!state.inference_enabled || ['complete','escalated'].includes(current.phase)))}
      onClick={() => void mutate('/api/continuation', {revision:state.incident!.revision, enabled:!active}, `continuation-${state.incident!.revision}-${active}-${current.expires ?? 'new'}`)}>
      {active ? 'Pause guided investigation' : 'Start guided investigation'}</button>
    <p className="caption">Starting authorizes up to {state.planning_remaining} remaining NVIDIA planning requests within the existing server/session allowance, for at most 30 minutes. Photo analysis requires its explicit action. No automatic retries, approvals or equipment actions.</p>
  </section>;
}
