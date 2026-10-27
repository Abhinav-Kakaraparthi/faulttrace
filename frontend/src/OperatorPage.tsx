import type { WorkspaceProps } from './workspace';
import { WorkspaceState } from './WorkspaceState';
import { ServerTask } from './ServerTask';
import { JourneyPanel } from './JourneyPanel';
import { EvidenceWorkspace } from './EvidenceWorkspace';
import { PhotoFollowUp } from './PhotoPlanning';
import { AuditHistory } from './AuditHistory';

export function OperatorPage(props: WorkspaceProps) {
  const { state, connection, disabled, mutate } = props;
  const completed = state?.journey && state.journey.maintenance_status !== 'not_completed';
  const actionAssigned = state?.journey?.approval_current && !completed;
  return <main id="main-content" tabIndex={-1} className="operator-layout connected-operator operator-page">
    <header className="operator-intro"><span className="eyebrow">OPERATOR / FIELD TASK</span><h1>{completed ? 'Simulated correction and recovery record' : state?.task ? `${state.task.asset_id} · Observation task` : 'Assigned work'}</h1>
      {state?.incident && <details className="incident-context"><summary>Incident details</summary><p>Shared incident {state.incident.id} / evidence revision {state.incident.revision}. Human observations and approved simulated assignments only; no real equipment control.</p></details>}
    </header>
    {state?.journey?.test_output && <p className="notice">OFFLINE TEST OUTPUT / provider doubles, no live AI or real token consumption.</p>}
    <WorkspaceState state={state} connection={connection} workspace="operator" />
    {state?.incident && <>
      {state.task && !completed && !actionAssigned && <section aria-label="Assigned observation"><ServerTask key={`${state.task.id}-${state.task.revision}`} state={state} mutate={mutate} disabled={disabled} inspect={props.inspect} />
        {state.journey && state.journey.evidence_mode !== 'task-evidence' && <p className="notice">This NVIDIA observation task is separate from the simulated correction checklist below. Its evidence is not yet integrated into that deterministic assessment.</p>}
      </section>}
      {!completed && !actionAssigned && <PhotoFollowUp state={state} disabled={disabled} mutate={mutate} inspect={props.inspect} />}
      {state.journey && <JourneyPanel state={state} view="operator" presentation="operator" includeRecord={false} mutate={mutate} disabled={disabled} />}
      {!state.task && !state.journey && <ServerTask state={state} mutate={mutate} disabled={disabled} inspect={props.inspect} />}
      <EvidenceWorkspace {...props} workspace="operator" />
      <details className="section-surface operator-history"><summary>Incident audit history</summary><AuditHistory state={state} /></details>
    </>}
  </main>;
}
