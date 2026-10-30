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
import { DemoObservations } from './DemoObservations';
import { DocumentationLookup } from './DocumentationLookup';
import { InvestigationActivity } from './InvestigationActivity';
import { investigationStage } from './investigationStage';
import { GuidedInvestigation } from './GuidedInvestigation';

export function CommanderPage(props: WorkspaceProps) {
  const { state, connection, disabled, mutate, navigate } = props;
  const [equipment, select] = useState<Equipment>('F-17');
  const j = state?.journey;
  const sample = j?.samples.at(-1);
  const stage = state ? investigationStage(state, 'commander') : null;
  const correctionFocus = stage?.key === 'approval' || stage?.key === 'recovery_verification';
  const planner = state && <PlannerPanel inspect={props.inspect} state={state} disabled={disabled || !!state.continuation?.enabled} historyOnly={correctionFocus} choose={() => void mutate('/api/planning', { revision: state.incident!.revision }, `plan-${state.incident!.revision}`)} open={() => navigate('/operator')} />;
  const journey = state && j && <JourneyPanel release={props.release} state={state} view="commander" presentation="commander" includeRecord={false} showOutcome={false} mutate={mutate} disabled={disabled} />;
  return <main id="main-content" tabIndex={-1} className="commander commander-page">
    <header className="page-heading"><div><span className="eyebrow">COMMANDER / INVESTIGATION</span><h1>{state?.incident ? 'Return-flow investigation' : 'Commander workspace'}</h1>
      {(state?.test_output || j?.test_output) && <span className="workspace-test-label">OFFLINE TEST OUTPUT · no live AI</span>}
      <details className="incident-context"><summary>Incident &amp; workspace details</summary>
        <p>Review sources, choose observations, approve only a registered simulated correction and inspect independent recovery.</p>
        {state?.incident && <p>Shared incident {state.incident.id} / evidence revision {state.incident.revision}</p>}</details></div>
      {(props.canCreate ?? !props.release) && !state?.incident && <div className="incident-actions"><button className="button primary" disabled={!(props.creationReady ?? !disabled)} onClick={() => void mutate('/api/investigations', {}, 'start-synthetic-journey')}>Start restriction-to-recovery simulation</button><button className="button secondary" disabled={!(props.creationReady ?? !disabled)} onClick={() => void mutate('/api/incidents', {}, 'start-incident')}>Start observation-only incident</button></div>}
      {!props.release && <a className="button secondary" href="/operator" onClick={e => { if (!e.ctrlKey && !e.metaKey && !e.shiftKey && !e.altKey && e.button === 0) { e.preventDefault(); navigate('/operator'); } }}>Open Operator workspace</a>}
    </header>
    <WorkspaceState state={state} connection={connection} workspace="commander" />
    {state?.incident && <>
      <GuidedInvestigation state={state} mutate={mutate} disabled={disabled} />
      <InvestigationActivity state={state} view="commander" />
      <div className="commander-overview-grid"><aside className="current-action section-surface" aria-label="Current investigation action"><span className="eyebrow">{correctionFocus ? 'DETERMINISTIC POLICY / NEXT ACTION' : 'NVIDIA OBSERVATION PLANNING'}</span>
          {correctionFocus ? journey : planner}<DemoObservations {...props} />
          <details className="model-scope"><summary>AI role and evidence boundaries</summary><p>Text proposals choose registered observations or human escalation. Image analysis produces interpretations, not diagnosis, correction approval or recovery declarations.</p>
          {j && j.evidence_mode !== 'task-evidence' && <p className="notice">Separate workflow: NVIDIA task evidence does not currently satisfy the simulated correction assessment. Recovery is evaluated independently from simulator samples; no integrated model recovery reasoning is claimed.</p>}</details>
        </aside><div className="process-and-signals"><ServerTelemetry compact samples={j?.samples ?? []} /><Process active selected={equipment} onSelect={select} readings={{ pressure: sample?.pressure ?? null, valve: sample?.valve ?? null }} /></div></div>
      {j && !correctionFocus && <details className="section-surface investigation-detail"><summary>Deterministic assessment and correction conditions</summary>{journey}</details>}
      {correctionFocus && <details className="section-surface investigation-detail"><summary>NVIDIA observation planning history</summary>{planner}</details>}
      {!j && <section className="section-surface"><h2>Evidence assessment</h2><p>Restriction, sensor discrepancy and valve mismatch remain hypotheses. No deterministic recovery assessment is available for this observation-only incident; model interpretations retain their provenance below.</p></section>}
      <EvidenceWorkspace {...props} workspace="commander" /><details className="section-surface investigation-detail"><summary>Chronological activity and audit</summary><AuditHistory state={state} /></details>
      {state.documentation && props.access && <DocumentationLookup access={props.access} revision={state.incident.revision} enabled={!disabled && state.documentation.enabled} />}
      {state.demo?.spending && <details className="section-surface"><summary>Server inference allowance</summary><p>{state.demo.spending.requests_reserved} of {state.demo.spending.request_limit} visitor requests reserved. {state.demo.spending.token_allowance_consumed} of {state.demo.spending.token_allowance_limit} token-admission units consumed; {state.demo.spending.uncertain_or_pending} uncertain or pending.</p><p>{state.demo.spending.label}. Full allowances remain charged even when usage is missing. Actual provider usage remains in individual receipts.</p></details>}
    </>}
  </main>;
}
