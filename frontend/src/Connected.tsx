import { useEffect, useRef, useState } from 'react';
import { type Equipment, type View } from './demo';
import { type ServerEvidence } from './api';
import { useWorkflow } from './useWorkflow';
import { PlannerPanel } from './PlannerPanel';
import { ServerTask } from './ServerTask';
import { ServerEvidenceDetails, ServerEvidenceList } from './ServerEvidence';
import { Process, Telemetry } from './Process';
import { AuditHistory } from './AuditHistory';
import { JourneyPanel } from './JourneyPanel';
import { Icon } from './Icon';

export function Connected() {
  const server = useWorkflow();
  const [view, setView] = useState<View>(new URLSearchParams(location.search).get('view') === 'operator' ? 'operator' : 'commander');
  const [equipment, setEquipment] = useState<Equipment>('F-17');
  const [inspected, inspect] = useState<ServerEvidence | null>(null);
  const dialog = useRef<HTMLDialogElement>(null);
  const focusReturn = useRef<HTMLElement | null>(null);
  useEffect(() => { if (inspected) dialog.current?.showModal(); }, [inspected]);
  function switchView(next: View) {
    setView(next);
    const url = new URL(location.href); url.searchParams.set('view', next); history.replaceState(null, '', url);
    window.scrollTo({ top: 0 });
    requestAnimationFrame(() => document.getElementById('main-content')?.focus({ preventScroll: true }));
  }
  function open(item: ServerEvidence) { focusReturn.current = document.activeElement as HTMLElement; inspect(item); }
  function close() { dialog.current?.close(); inspect(null); focusReturn.current?.focus(); }
  const state = server.state;
  const disabled = server.busy || server.connection !== 'online';
  const task = state?.task;
  const journeyTerminal = state?.journey?.recovery.status === 'verified' || state?.journey?.recovery.status === 'failed';
  const analyze = (item: ServerEvidence) => {
    if (task) void server.mutate(`/api/evidence/${item.id}/analyze`, { revision: task.revision }, `analysis-${item.id}-${task.revision}`);
  };
  return <div className="app-shell connected-shell"><a className="skip-link" href="#main-content">Skip to workspace</a>
    <aside className="sidebar"><div className="brand"><span className="brand-mark"><Icon name="trace" /></span>FaultTrace.</div><p className="tagline">Trace the cause.<br />Verify the recovery.</p><nav aria-label="Server workspace views">{(['commander', 'operator'] as const).map(value => <button key={value} aria-current={view === value ? 'page' : undefined} onClick={() => switchView(value)}><Icon name={value === 'commander' ? 'grid' : 'phone'} />{value === 'commander' ? 'Commander' : 'Operator'}</button>)}</nav><div className="sidebar-bottom"><strong>Local server workflow</strong><span>SQLite · one local instance</span><span>No equipment control</span></div></aside>
    <div className="workspace"><div className="demo-banner"><span>Simulated incident & telemetry · local server</span><span>Real inference only on explicit planning / analysis</span></div>
      <header className="topbar"><span className="mobile-brand">FaultTrace.</span><span className="breadcrumb">Server: {server.connection === 'online' ? 'connected locally' : server.connection === 'loading' ? 'loading…' : 'unavailable / polling paused'}</span><button className="button quiet" onClick={server.refresh}>Refresh server state</button></header>
      <div className="mobile-switch" role="group" aria-label="Server workspace views">{(['commander', 'operator'] as const).map(value => <button key={value} aria-pressed={view === value} onClick={() => switchView(value)}>{value === 'commander' ? 'Commander' : 'Operator'}</button>)}</div>
      {server.connection === 'paused' && <p className="connection-warning" role="status">Connection interrupted. Displayed data may be stale; writes are disabled. Refresh to reconnect. No analysis will be retried automatically.</p>}
      {server.error && <p className="connection-warning" role="alert">{server.error}</p>}
      <main id="main-content" tabIndex={-1} className={view === 'operator' ? 'operator-layout connected-operator' : 'commander'}>
        <div className="page-heading"><div><h1>{!state ? 'Connecting to local workflow' : !state.incident ? 'No active incident' : state.journey ? (journeyTerminal ? 'Simulated recovery / outcome review' : view === 'operator' ? 'Operator / simulated journey' : 'Commander / simulated investigation') : view === 'operator' ? `${task?.asset_id ?? 'Operator'} · Observation task` : 'Simulated incident · Reduced return flow'}</h1><p>{!state ? 'No server data is available yet; sample results are never substituted here.' : state.journey ? 'Local simulation only. Measurements, operator reports and the audit record remain available in both views.' : state.incident ? 'Simulated telemetry. Model proposals require application validation; observations never prove recovery.' : 'Start a simulated incident, then explicitly choose an observation.'}</p></div>
          {view === 'commander' && state && !state.incident && <button className="button primary" disabled={disabled} onClick={() => void server.mutate('/api/simulation/start', {}, 'start-synthetic-journey')}>Start restriction-to-recovery simulation</button>}
          {view === 'commander' && !state?.incident && <button className="button primary" disabled={disabled || !state} onClick={() => void server.mutate('/api/incidents', {}, 'start-incident')}>Start simulated incident</button>}
          {view === 'commander' && state?.incident && <a className="button secondary" href="/?mode=connected&view=operator" target="_blank" rel="noreferrer">Open operator tab ↗</a>}
        </div>
        {!state && <section className="section-surface connected-empty"><h2>{server.connection === 'loading' ? 'Loading server state…' : 'Backend is not available'}</h2><p>Start the local backend using the startup guide. Sample preview remains a separate mode; no results are substituted here.</p></section>}
        {state && !state.incident && <section className="section-surface connected-empty"><h2>{view === 'operator' ? 'No observation task assigned' : 'Ready for a simulated investigation'}</h2><p>No fault explanation or model reading exists before the incident starts. Open this server workflow in a second tab to share the same task.</p></section>}
        {state?.incident && <>
          {state.journey && <JourneyPanel state={state} view={view} mutate={server.mutate} disabled={disabled} />}
          {!state.journey && <>
          {view === 'operator' ? <><PlannerPanel state={state} disabled={disabled} choose={() => void server.mutate('/api/planning', { revision: state.incident!.revision }, `plan-${state.incident!.revision}`)} open={() => document.getElementById('operator-assignment')?.focus()} /><div id="operator-assignment" tabIndex={-1}><ServerTask key={task ? `${task.id}-${task.revision}` : 'no-task'} state={state} mutate={server.mutate} disabled={disabled} /></div></> : <>
            <div className="readings"><div><span className="metric-label">SIMULATED RETURN FLOW</span><strong>86 <small>m³/h</small></strong><span className="metric-note">Fixed simulation sample</span></div><div><span className="metric-label">SIMULATED DIFFERENTIAL PRESSURE</span><strong>184 <small>kPa</small></strong><span className="metric-note">Not live telemetry</span></div><div><span className="metric-label">SIMULATED VALVE FEEDBACK</span><strong>72 <small>%</small></strong><span className="metric-note">Physical position unverified</span></div></div>
            <div className="workspace-grid"><PlannerPanel state={state} disabled={disabled} choose={() => void server.mutate('/api/planning', { revision: state.incident!.revision }, `plan-${state.incident!.revision}`)} open={() => switchView('operator')} />
              <div className="main-column"><Process active selected={equipment} onSelect={setEquipment} /><Telemetry active /></div><section className="investigation section-surface connected-explanations"><h2>Keep the investigation open</h2><p>Restriction, sensor discrepancy, and valve mismatch remain untested alternatives. No provider output selects a diagnosis or declares recovery.</p></section></div>
          </>}
          </>}
          {state.journey && <details className="section-surface journey-planner"><summary>{journeyTerminal ? 'Observation planning history (separate workflow)' : 'Optional NVIDIA observation planner (separate from correction policy)'}</summary><p>No inference is needed for the simulated journey. Existing opt-in and four-turn budget apply.</p><PlannerPanel historyOnly={journeyTerminal} state={state} disabled={disabled} choose={() => void server.mutate('/api/planning', { revision: state.incident!.revision }, `plan-${state.incident!.revision}`)} open={() => switchView('operator')} />{!journeyTerminal && state.task && <ServerTask key={`${state.task.id}-${state.task.revision}`} state={state} mutate={server.mutate} disabled={disabled} />}</details>}
          {state.journey ? <details className="section-surface journey-other-evidence"><summary>Image and planner-task evidence ({state.evidence.length})</summary><ServerEvidenceList state={state} inspect={open} analyze={analyze} disabled={disabled} /></details> : <ServerEvidenceList state={state} inspect={open} analyze={analyze} disabled={disabled} />}
          <AuditHistory state={state} />
        </>}
      </main>
    </div><dialog ref={dialog} className="evidence-dialog" aria-label="Server evidence inspection" onCancel={event => { event.preventDefault(); close(); }} onClose={() => inspect(null)}><div className="dialog-heading"><h2>Server evidence</h2><button className="icon-button" aria-label="Close evidence inspection" onClick={close}><Icon name="close" /></button></div>{inspected && <ServerEvidenceDetails evidence={state?.evidence.find(item => item.id === inspected.id) ?? inspected} />}</dialog>
  </div>;
}
