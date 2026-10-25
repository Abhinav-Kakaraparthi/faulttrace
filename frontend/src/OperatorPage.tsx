import type { WorkspaceProps } from './workspace';
import { WorkspaceState } from './WorkspaceState';
import { ServerTask } from './ServerTask';
import { JourneyPanel } from './JourneyPanel';
import { EvidenceWorkspace } from './EvidenceWorkspace';
import { AuditHistory } from './AuditHistory';

export function OperatorPage(props: WorkspaceProps) {
  const { state, connection, disabled, mutate } = props;
  return <main id="main-content" tabIndex={-1} className="operator-layout connected-operator operator-page">
    <header className="operator-intro"><span className="eyebrow">OPERATOR / FIELD TASK</span><h1>Assigned work</h1><p>Observe, report evidence gaps and complete only an approved simulated assignment. No real equipment control.</p>
      {state?.incident && <p className="caption">Shared incident {state.incident.id} / evidence revision {state.incident.revision}</p>}
    </header>
    <WorkspaceState state={state} connection={connection} workspace="operator" />
    {state?.incident && <>
      {state.task && <section aria-label="Assigned observation"><ServerTask key={`${state.task.id}-${state.task.revision}`} state={state} mutate={mutate} disabled={disabled} />
        {state.journey && <p className="notice">This NVIDIA observation task is separate from the simulated correction checklist below. Its evidence is not yet integrated into that deterministic assessment.</p>}
      </section>}
      {state.journey && <JourneyPanel state={state} view="operator" presentation="operator" includeRecord={false} mutate={mutate} disabled={disabled} />}
      {!state.task && !state.journey && <ServerTask state={state} mutate={mutate} disabled={disabled} />}
      <EvidenceWorkspace {...props} workspace="operator" />
      <details className="section-surface operator-history"><summary>Incident audit history</summary><AuditHistory state={state} /></details>
    </>}
  </main>;
}
