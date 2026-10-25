import type { ServerState } from './api';
import type { JourneyState } from './journeyState';
import { recoveryLabel } from './journeyState';

export function nextJourneyAction(j: JourneyState, view: 'commander' | 'operator'): string {
  if (j.recovery.status === 'verified') return view === 'operator'
    ? 'No further operator action is required for this simulated run. Review the evidence and recovery record.'
    : 'Review the verified recovery and its evidence. Real diagnosis and maintenance sign-off remain outside this simulation.';
  if (j.recovery.status === 'failed') return 'Review the failed verification and escalate for human investigation. No automatic correction or retry.';
  if (j.maintenance_status !== 'not_completed') return view === 'operator' ? 'Completion acknowledged. Commander will collect the post-correction verification samples.' : 'Advance the simulation to collect the next post-correction sample. Completion alone does not prove recovery.';
  if (j.approval_current) return view === 'operator' ? 'Complete the approved simulated filter replacement.' : 'Approval is recorded. Operator must complete the simulated correction before recovery can be assessed.';
  if (j.assessment.eligible) return view === 'commander' ? 'Review the working diagnosis and approve or decline the simulated correction.' : 'Required evidence is recorded. Commander must review and approve the current revision.';
  return view === 'operator' ? 'Record the required F-17 pressure and V-08 position observations, or report a genuine evidence gap.' : 'Review the evidence gaps. Operator observations are required before correction approval.';
}

export function JourneyOutcome({ state, view }: { state: ServerState; view: 'commander' | 'operator' }) {
  const j = state.journey!;
  const completed = j.maintenance_status !== 'not_completed';
  const approval = state.events.filter(e => e.kind === 'simulated_correction_approved').at(-1);
  const execution = state.events.filter(e => e.kind === 'simulated_filter_replacement_completed').at(-1);
  return <section className={`journey-outcome ${j.recovery.status}`} aria-labelledby="journey-outcome-title">
    <span className="eyebrow">{view === 'operator' ? 'OPERATOR / NEXT ACTION' : 'COMMANDER / DECISION'}</span>
    <h3 id="journey-outcome-title">{completed ? recoveryLabel(j.recovery.status) : 'Evidence first. Human approval next.'}</h3>
    <p className="journey-next-action">{nextJourneyAction(j, view)}</p>
    {completed && <><dl className="journey-outcome-facts">
      <div><dt>Evidence</dt><dd>{j.observations.length} simulated human observations; {j.approved_evidence_refs.length} approval references</dd></div>
      <div><dt>Maintenance</dt><dd>Simulated replacement completed</dd></div>
      <div><dt>Independent verification</dt><dd>{j.recovery.sample_count} post-action samples spanning {j.recovery.window_seconds} simulated seconds</dd></div>
    </dl><details><summary>Approval and completion audit summary</summary>
      <p>Wall-clock audit times (UTC) record when the user actions were saved. They are not simulated measurement times.</p>
      <p>Approval recorded: {approval ? <time dateTime={approval.created_at}>{approval.created_at}</time> : 'Not available in this snapshot'}</p>
      <p>Simulated completion recorded: {execution ? <time dateTime={execution.created_at}>{execution.created_at}</time> : 'Not available in this snapshot'}</p>
      <p>Recovery is evaluated from stored measurements, not from the completion event. No separate recovery audit event is invented.</p>
    </details></>}
    <p className="caption">Simulation only. Deterministic assessment and verification; no model diagnosis, real equipment action or real maintenance sign-off.</p>
  </section>;
}
