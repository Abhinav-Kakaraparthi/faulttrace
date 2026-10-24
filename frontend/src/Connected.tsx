import { useEffect, useRef, useState } from 'react';
import { type Equipment, type View } from './demo';
import { type ServerEvidence } from './api';
import { useWorkflow } from './useWorkflow';
import { ServerTask } from './ServerTask';
import { ServerEvidenceDetails, ServerEvidenceList } from './ServerEvidence';
import { Process, Telemetry } from './Process';
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
  const analyze = (item: ServerEvidence) => {
    if (task) void server.mutate(`/api/evidence/${item.id}/analyze`, { revision: task.revision }, `analysis-${item.id}-${task.revision}`);
  };
  return <div className="app-shell connected-shell"><a className="skip-link" href="#main-content">Skip to workspace</a>
    <aside className="sidebar"><div className="brand"><span className="brand-mark"><Icon name="trace" /></span>FaultTrace.</div><p className="tagline">Trace the cause.<br />Verify the recovery.</p><nav aria-label="Server workspace views">{(['commander', 'operator'] as const).map(value => <button key={value} aria-current={view === value ? 'page' : undefined} onClick={() => switchView(value)}><Icon name={value === 'commander' ? 'grid' : 'phone'} />{value === 'commander' ? 'Commander' : 'Operator'}</button>)}</nav><div className="sidebar-bottom"><strong>Local server workflow</strong><span>SQLite · one local instance</span><span>No equipment control</span></div></aside>
    <div className="workspace"><div className="demo-banner"><span>Simulated incident & telemetry · local server</span><span>Real Nebius inference only on Analyze image</span></div>
      <header className="topbar"><span className="mobile-brand">FaultTrace.</span><span className="breadcrumb">Server: {server.connection === 'online' ? 'connected locally' : server.connection === 'loading' ? 'loading…' : 'unavailable / polling paused'}</span><button className="button quiet" onClick={server.refresh}>Refresh server state</button></header>
      <div className="mobile-switch" role="group" aria-label="Server workspace views">{(['commander', 'operator'] as const).map(value => <button key={value} aria-pressed={view === value} onClick={() => switchView(value)}>{value === 'commander' ? 'Commander' : 'Operator'}</button>)}</div>
      {server.connection === 'paused' && <p className="connection-warning" role="status">Connection interrupted. Displayed data may be stale; writes are disabled. Refresh to reconnect. No analysis will be retried automatically.</p>}
      {server.error && <p className="connection-warning" role="alert">{server.error}</p>}
      <main id="main-content" tabIndex={-1} className={view === 'operator' ? 'operator-layout connected-operator' : 'commander'}>
        <div className="page-heading"><div><h1>{!state ? 'Connecting to local workflow' : !state.incident ? 'No active incident' : view === 'operator' ? 'F-17 · Observation task' : 'Simulated incident · Reduced return flow'}</h1><p>{!state ? 'No server data is available yet; sample results are never substituted here.' : state.incident ? 'Fixed simulation workflow. Model readings are interpretations, never a diagnosis or verified recovery.' : 'Start one simulated incident to assign a server-backed observation task.'}</p></div>
          {view === 'commander' && !state?.incident && <button className="button primary" disabled={disabled || !state} onClick={() => void server.mutate('/api/incidents', {}, 'start-incident')}>Start simulated incident</button>}
          {view === 'commander' && state?.incident && <a className="button secondary" href="/?mode=connected&view=operator" target="_blank" rel="noreferrer">Open operator tab ↗</a>}
        </div>
        {!state && <section className="section-surface connected-empty"><h2>{server.connection === 'loading' ? 'Loading server state…' : 'Backend is not available'}</h2><p>Start the local backend using the startup guide. Sample preview remains a separate mode; no results are substituted here.</p></section>}
        {state && !state.incident && <section className="section-surface connected-empty"><h2>{view === 'operator' ? 'No observation task assigned' : 'Ready for a simulated investigation'}</h2><p>No fault explanation or model reading exists before the incident starts. Open this server workflow in a second tab to share the same task.</p></section>}
        {state?.incident && task && <>
          {view === 'operator' ? <ServerTask key={`${task.id}-${task.revision}`} state={state} mutate={server.mutate} disabled={disabled} /> : <>
            <div className="readings"><div><span className="metric-label">SIMULATED RETURN FLOW</span><strong>86 <small>m³/h</small></strong><span className="metric-note">Fixed simulation sample</span></div><div><span className="metric-label">SIMULATED DIFFERENTIAL PRESSURE</span><strong>184 <small>kPa</small></strong><span className="metric-note">Not live telemetry</span></div><div><span className="metric-label">SIMULATED VALVE FEEDBACK</span><strong>72 <small>%</small></strong><span className="metric-note">Physical position unverified</span></div></div>
            <div className="workspace-grid"><section className="observation-task section-surface"><span className="eyebrow">SERVER TASK · FIXED SIMULATION WORKFLOW</span><h2>F-17 · Read local pressure</h2><p>Requested evidence: display and unit, or an honest refusal/unreadable report.</p><span className="pill amber">{task.status} · revision {task.revision}</span><details className="rationale"><summary>Why this task?</summary><p>Compare a local image with simulated flow and pressure. The task is fixed, not AI planning.</p></details><button className="button primary wide" onClick={() => switchView('operator')}>Open operator task</button>{!['awaiting', 'analyzing'].includes(task.status) && <button className="button secondary wide repeat-observation" disabled={disabled} onClick={() => void server.mutate(`/api/tasks/${task.id}/reopen`, { revision: task.revision }, `reopen-${task.id}-${task.revision}`)}>Request another observation</button>}</section>
              <div className="main-column"><Process active selected={equipment} onSelect={setEquipment} /><Telemetry active /></div><section className="investigation section-surface connected-explanations"><h2>Keep the investigation open</h2><p>Restriction, sensor discrepancy, and valve mismatch remain untested alternatives. No provider output selects a diagnosis or declares recovery.</p></section></div>
          </>}
          <ServerEvidenceList state={state} inspect={open} analyze={analyze} disabled={disabled} />
          <section className="section-surface connected-events"><h2>Server activity</h2><ol>{state.events.map(event => <li key={event.sequence}><strong>{event.kind.replaceAll('_', ' ')}</strong><time dateTime={event.created_at}>{new Date(event.created_at).toLocaleString()}</time></li>)}</ol></section>
        </>}
      </main>
    </div><dialog ref={dialog} className="evidence-dialog" aria-label="Server evidence inspection" onCancel={event => { event.preventDefault(); close(); }} onClose={() => inspect(null)}><div className="dialog-heading"><h2>Server evidence</h2><button className="icon-button" aria-label="Close evidence inspection" onClick={close}><Icon name="close" /></button></div>{inspected && <ServerEvidenceDetails evidence={state?.evidence.find(item => item.id === inspected.id) ?? inspected} />}</dialog>
  </div>;
}
