import type { WorkspaceProps } from './workspace';
import { WorkspaceState } from './WorkspaceState';
import { ServerTask } from './ServerTask';
import { JourneyPanel } from './JourneyPanel';
import { EvidenceWorkspace } from './EvidenceWorkspace';
import { PhotoFollowUp } from './PhotoPlanning';
import { AuditHistory } from './AuditHistory';
import { InvestigationActivity } from './InvestigationActivity';
import { investigationStage } from './investigationStage';

export function OperatorPage(props: WorkspaceProps) {
  const { state, connection, disabled, mutate } = props;
  const completed = state?.journey && state.journey.maintenance_status !== 'not_completed';
  const actionAssigned = state?.journey?.approval_current && !!state.journey.approval_id && !completed;
  const previousOnly = state && ['human_escalation', 'approval'].includes(investigationStage(state, 'operator').key)
    && state.task && !['awaiting', 'needs_evidence', 'submitted', 'analyzing'].includes(state.task.status);
  const observation = state?.task && <section aria-label="Assigned observation"><ServerTask key={state.task.id} state={state} mutate={mutate} disabled={disabled} inspect={props.inspect} submitPhoto={props.submitPhoto} allowFixtures={props.release === false} />
    {state.journey && state.journey.evidence_mode !== 'task-evidence' && <p className="notice">This NVIDIA observation task is separate from the simulated correction checklist below. Its evidence is not yet integrated into that deterministic assessment.</p>}</section>;
  return <main id="main-content" tabIndex={-1} className="operator-layout connected-operator operator-page">
    <header className="operator-intro"><span className="eyebrow">OPERATOR / FIELD WORKSPACE</span><h1>{completed ? 'Simulated correction and recovery record' : state?.task ? `${state.task.asset_id} · Observation task` : 'Assigned work'}</h1>
      {(state?.test_output || state?.journey?.test_output) && <span className="workspace-test-label">OFFLINE TEST OUTPUT · no live AI</span>}
      {state?.incident && <details className="incident-context"><summary>Incident details</summary><p>Shared incident {state.incident.id} / evidence revision {state.incident.revision}. Human observations and approved simulated assignments only; no real equipment control.</p></details>}
    </header>
    <WorkspaceState state={state} connection={connection} workspace="operator" />
    {state?.incident && <>
      <InvestigationActivity state={state} view="operator" />
      {state.task && !completed && !actionAssigned && (previousOnly ? <details className="section-surface investigation-detail"><summary>Previous observation assignment</summary>{observation}</details> : observation)}
      {!completed && !actionAssigned && <PhotoFollowUp state={state} disabled={disabled} mutate={mutate} inspect={props.inspect} />}
      {!state.task && !completed && !actionAssigned && <ServerTask state={state} mutate={mutate} disabled={disabled} inspect={props.inspect} />}
      {state.journey && (completed || actionAssigned ? <JourneyPanel release={props.release} state={state} view="operator" presentation="operator" includeRecord={false} showOutcome={false} mutate={mutate} disabled={disabled} /> : <details className="section-surface investigation-detail"><summary>Evidence assessment and simulation details</summary><JourneyPanel release={props.release} state={state} view="operator" presentation="operator" includeRecord={false} showOutcome={false} mutate={mutate} disabled={disabled} /></details>)}
      <EvidenceWorkspace {...props} workspace="operator" />
      <details className="section-surface operator-history"><summary>Incident audit history</summary><AuditHistory state={state} /></details>
    </>}
  </main>;
}
