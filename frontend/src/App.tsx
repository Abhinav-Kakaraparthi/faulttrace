import { useEffect, useReducer, useRef, useState } from 'react';
import { initial, reduceDemo, type Equipment, type Evidence, type View } from './demo';
import { Icon } from './Icon';
import { Process, Telemetry } from './Process';
import { ActivityPanel, EvidenceDialog, Investigation } from './Investigation';
import { Operator } from './Operator';
import { ObservationTask } from './ObservationTask';

export function SamplePreview() {
  const [demo, dispatch] = useReducer(reduceDemo, initial);
  const [view, setView] = useState<View>('commander');
  const [selected, select] = useState<Equipment>('F-17');
  const [evidence, setEvidence] = useState<Evidence | null>(null);
  const dialog = useRef<HTMLDialogElement>(null);
  const trigger = useRef<HTMLElement | null>(null);
  useEffect(() => { if (evidence) dialog.current?.showModal(); }, [evidence]);
  function inspect(item: Evidence) { trigger.current = document.activeElement as HTMLElement; setEvidence(item); }
  function close() { dialog.current?.close(); setEvidence(null); trigger.current?.focus(); }
  function switchView(next: View) {
    setView(next); window.scrollTo({ top: 0 });
    requestAnimationFrame(() => document.getElementById('main-content')?.focus({ preventScroll: true }));
  }
  function reset() { dispatch({ type: 'reset' }); select('F-17'); setEvidence(null); setView('commander'); }
  return <div className="app-shell"><a className="skip-link" href="#main-content">Skip to workspace</a>
    <aside className="sidebar"><div className="brand"><span className="brand-mark"><Icon name="trace" size={25} /></span>FaultTrace<span className="brand-period">.</span></div><p className="tagline">Trace the cause.<br />Verify the recovery.</p><span className="sidebar-label">WORKSPACE</span><nav aria-label="Workspace views"><button onClick={() => switchView('commander')} aria-current={view === 'commander' ? 'page' : undefined}><Icon name="grid" />Commander<span>01</span></button><button onClick={() => switchView('operator')} aria-current={view === 'operator' ? 'page' : undefined}><Icon name="phone" />Operator<span>02</span></button></nav><div className="sidebar-bottom"><div className="plant-icon">N</div><strong>North utility plant</strong><span>Sample environment</span><div className="local-status"><span className="status-dot teal-dot" /> Local browser state</div></div></aside>
    <div className="workspace"><div className="demo-banner"><span><span className="status-dot" /> Interactive demo — sample data</span><span>Live AI not connected <b>·</b> This browser only</span></div>
      <header className="topbar"><span className="mobile-brand">FaultTrace<span>.</span></span><div className="breadcrumb">North utility plant <span>/</span> Cooling system <span>/</span> <strong>{view === 'commander' ? 'Investigation' : 'Field observation'}</strong></div><button className="button quiet" onClick={reset}><Icon name="reset" size={16} />Reset demo</button></header>
      <div className="mobile-switch" role="group" aria-label="Workspace views"><button aria-pressed={view === 'commander'} onClick={() => switchView('commander')}>Commander</button><button aria-pressed={view === 'operator'} onClick={() => switchView('operator')}>Operator</button></div>
      {view === 'operator' ? <Operator key={`${demo.started}-${demo.waiting}-${demo.evidence.length}`} demo={demo} dispatch={dispatch} goCommander={() => switchView('commander')} inspect={inspect} /> : <main className="commander" id="main-content" tabIndex={-1}>
        <div className="page-heading"><div><h1>{demo.started ? 'INC-0042 · Reduced return flow' : 'No active demo incident'}</h1><p>{demo.started ? 'Compare rising filter pressure with local evidence before selecting a cause.' : 'Start a deterministic sample journey. No fault or cause has been established.'}</p></div><div className="incident-actions">{demo.started ? <span className="pill teal incident-status" role="status"><Icon name="check" size={16} />Demo incident active</span> : <button className="button primary" onClick={() => dispatch({ type: 'start' })}>Start demo incident<Icon name="arrow" size={18} /></button>}</div></div>
        <div className="readings" aria-label="Sample process readings"><div><span className="metric-label">RETURN FLOW <span>FT-04</span></span><strong>{demo.started ? '86' : '124'} <small>m³/h</small></strong><span className={demo.started ? 'metric-note amber-text' : 'metric-note'}>{demo.started ? '↓ 31% from sample baseline' : 'Sample baseline'}</span></div><div><span className="metric-label">DIFFERENTIAL PRESSURE <span>F-17</span></span><strong>{demo.started ? '184' : '62'} <small>kPa</small></strong><span className={demo.started ? 'metric-note amber-text' : 'metric-note'}>{demo.started ? '↑ 122 kPa from sample baseline' : 'Sample baseline'}</span></div><div><span className="metric-label">VALVE POSITION <span>V-08</span></span><strong>72 <small>%</small></strong><span className="metric-note">Feedback only · physical state unverified</span></div></div>
        <div className="workspace-grid"><ObservationTask demo={demo} goOperator={() => switchView('operator')} reopen={() => dispatch({ type: 'reopen' })} /><div className="main-column"><Process active={demo.started} selected={selected} onSelect={select} /><Telemetry active={demo.started} /></div><Investigation demo={demo} /></div>
        <ActivityPanel demo={demo} inspect={inspect} /><footer className="workspace-footer"><span>FAULTTRACE / INVESTIGATE WITH EVIDENCE</span><span>Sample data · no live AI, equipment control, or verified recovery</span></footer>
      </main>}
    </div><dialog ref={dialog} className="evidence-dialog" aria-label="Evidence inspection" onCancel={event => { event.preventDefault(); close(); }} onClose={() => setEvidence(null)}>{evidence && <EvidenceDialog evidence={evidence} close={close} />}</dialog>
  </div>;
}
