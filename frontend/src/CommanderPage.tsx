import { useState } from 'react';
import type { Equipment } from './demo';
import type { WorkspaceProps } from './workspace';
import { WorkspaceState } from './WorkspaceState';
import { Process } from './Process';
import { ServerTelemetry } from './ServerTelemetry';
import { JourneyPanel } from './JourneyPanel';
import { PlannerPanel } from './PlannerPanel';
import { EvidenceWorkspace } from './EvidenceWorkspace';
import { AuditHistory } from './AuditHistory';

export function CommanderPage(props: WorkspaceProps) {
  const { state, connection, disabled, mutate, navigate } = props;
  const [equipment, select] = useState<Equipment>('F-17');
  const j = state?.journey;
  const sample = j?.samples.at(-1);
  const terminal = j?.recovery.status === 'verified' || j?.recovery.status === 'failed';
  return <main id="main-content" tabIndex={-1} className="commander commander-page">
    <header className="page-heading"><div><span className="eyebrow">COMMANDER / INVESTIGATION & DECISIONS</span><h1>{state?.incident ? 'Investigation workspace' : 'Commander workspace'}</h1>
      <p>Review sources, choose observations, approve only a registered simulated correction and inspect independent recovery.</p>
      {state?.incident && <p className="caption">Shared incident {state.incident.id} / evidence revision {state.incident.revision}</p>}</div>
      {state && !state.incident && <div className="incident-actions"><button className="button primary" disabled={disabled} onClick={() => void mutate('/api/simulation/start', {}, 'start-synthetic-journey')}>Start restriction-to-recovery simulation</button><button className="button secondary" disabled={disabled} onClick={() => void mutate('/api/incidents', {}, 'start-incident')}>Start observation-only incident</button></div>}
      <a className="button secondary" href="/operator" onClick={e => { if (!e.ctrlKey && !e.metaKey && !e.shiftKey && !e.altKey && e.button === 0) { e.preventDefault(); navigate('/operator'); } }}>Open Operator workspace</a>
    </header>
    <WorkspaceState state={state} connection={connection} workspace="commander" />
    {state?.incident && <>
      {j && <JourneyPanel state={state} view="commander" presentation="commander" includeRecord={false} mutate={mutate} disabled={disabled} />}
      {!j && <section className="section-surface workspace-decision"><h2>Current decision: obtain an observation</h2><p>{state.task ? 'An observation is assigned. Review its state and wait for Operator evidence before requesting another.' : 'No task is assigned automatically. Choose a permitted observation or escalate for human investigation.'}</p></section>}
      <div className="commander-process-grid"><Process active selected={equipment} onSelect={select} readings={{ pressure: sample?.pressure ?? null, valve: sample?.valve ?? null }} /><ServerTelemetry samples={j?.samples ?? []} /></div>
      <section className="section-surface model-workflow"><h2>NVIDIA observation planning</h2><p>Text proposals choose registered observations or human escalation. Image analysis produces interpretations, not diagnosis, correction approval or recovery declarations.</p>
        {j && <p className="notice">Separate workflow: NVIDIA task evidence does not currently satisfy the simulated correction assessment. Recovery is evaluated independently from simulator samples; no integrated model recovery reasoning is claimed.</p>}
        <PlannerPanel state={state} disabled={disabled} historyOnly={terminal} choose={() => void mutate('/api/planning', { revision: state.incident!.revision }, `plan-${state.incident!.revision}`)} open={() => navigate('/operator')} />
      </section>
      {!j && <section className="section-surface"><h2>Evidence assessment</h2><p>Restriction, sensor discrepancy and valve mismatch remain hypotheses. No deterministic recovery assessment is available for this observation-only incident; model interpretations retain their provenance below.</p></section>}
      <EvidenceWorkspace {...props} workspace="commander" /><AuditHistory state={state} />
    </>}
  </main>;
}
