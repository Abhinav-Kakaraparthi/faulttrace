import type { ServerState } from './api';
import { investigationStage } from './investigationStage';
import { evidenceGapLabel } from './evidenceGapLabel';

const labels = { awaiting_planning: 'Awaiting planning', planning: 'Planning', observation: 'Assigned observation',
  evidence_review: 'Evidence review', human_escalation: 'Human escalation', approval: 'Approval', recovery_verification: 'Recovery verification' };

export function InvestigationActivity({ state, view }: { state: ServerState; view: 'commander' | 'operator' }) {
  const stage = investigationStage(state, view);
  const event = state.events.at(-1);
  const gaps = state.journey?.assessment.blockers ?? [];
  return <section className={`investigation-activity ${stage.tone} ${view}-activity`} aria-labelledby={`${view}-activity-title`}>
    <div className="activity-stage"><span className="stage-indicator" aria-hidden="true" /><span id={view === 'operator' ? `${view}-activity-title` : undefined}>{view === 'operator' ? stage.title : labels[stage.key]}</span>
      <span className="quiet-label">Simulated equipment</span></div>
    {view === 'commander' && <h2 id={`${view}-activity-title`}>{stage.title}</h2>}
    <p className="activity-next"><span>Next step</span>{stage.next}</p>
    {view === 'commander' && gaps.length > 0 && !['approval', 'recovery_verification'].includes(stage.key) &&
      <details className="activity-gaps"><summary>Evidence gaps ({gaps.length})</summary><ul>{gaps.map(code => <li key={code}>{evidenceGapLabel(code)}</li>)}</ul><p>Deterministic assessment; not model diagnosis.</p></details>}
    {view === 'commander' && event && <p className="activity-event"><span>Last saved activity</span>{event.kind.replaceAll('_', ' ')}
      <time dateTime={event.created_at}>{event.created_at}</time><small>Wall-clock audit time · not a simulated measurement</small></p>}
  </section>;
}
