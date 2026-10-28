import { useState } from 'react';
import { type ServerState } from './api';
import { approvalBlocker, canApprove, canExecute, recoveryLabel } from './journeyState';
import panelA from '../../fixtures/image-evidence/panel-a.png';
import { JourneyRecord } from './JourneyRecord';
import { JourneyOutcome } from './JourneyOutcome';
import './journey.css';

type Mutate = (path: string, body: object, identity: string) => Promise<boolean>;
export function JourneyPanel({ state, view, mutate, disabled, presentation = 'full', includeRecord = true, release = false }: {
  release?: boolean;
  presentation?: 'full' | 'commander' | 'operator'; includeRecord?: boolean;
  state: ServerState; view: 'commander' | 'operator'; mutate: Mutate; disabled: boolean;
}) {
  const [pressure, setPressure] = useState('');
  const [pressureStatus, setPressureStatus] = useState('readable');
  const [position, setPosition] = useState('');
  const [consent, setConsent] = useState<number | null>(null);
  const [message, setMessage] = useState('');
  const j = state.journey;
  if (!j || !state.incident) return null;
  const revision = state.incident.revision;
  const completed = j.maintenance_status !== 'not_completed';
  const sample = j.samples.at(-1);
  const terminal = j.recovery.status === 'verified' || j.recovery.status === 'failed';
  const blocker = approvalBlocker(j);
  async function act(operation: string, body: object, identity = operation) {
    setMessage('');
    const ok = await mutate(`/api/simulation/${operation}`, { revision, ...body }, `journey-${identity}-${revision}`);
    if (ok) { setMessage('Saved to this local simulation.'); setConsent(null); }
  }
  async function reportPressure() {
    const reading = pressureStatus === 'readable' ? Number(pressure) : null;
    if (pressureStatus === 'readable' && (!pressure.trim() || !Number.isFinite(reading) || reading! < 0 || reading! > 1000)) {
      setMessage('Enter a finite synthetic reading from 0 to 1000 kPa.'); return;
    }
    await act('observe', { asset_id: 'F-17', status: pressureStatus, reading }, `pressure-${pressureStatus}-${pressure}`);
  }
  const advance = <div className="journey-clock"><span>Simulation clock (UTC)</span><time dateTime={j.clock}>{j.clock}</time>
    <button className="button secondary" disabled={disabled || j.tick >= 360} onClick={() => void act('advance', {})}>Advance 10 simulated seconds</button>
    <small>Explicit steps, no background clock. New samples can invalidate approval or change recovery status.</small></div>;
  const verification = <div className={`journey-verification ${j.recovery.status}`} role="status">
    <h4>{recoveryLabel(j.recovery.status)}</h4><p>{j.recovery.sample_count} post-correction samples / {j.recovery.window_seconds} simulated seconds observed / {j.policy.window_seconds}s minimum</p>
    <progress max={j.policy.window_seconds} value={Math.min(j.recovery.window_seconds, j.policy.window_seconds)} aria-label="Recovery observation window" />
    <p>{j.recovery.status === 'failed' ? 'Recovery was not sustained. Review the measurements and escalate; no automatic retry.' : 'Recovery comes only from qualifying post-action measurements. Later out-of-band samples can revoke verification.'}</p>
  </div>;
  return <section className="journey" aria-labelledby="journey-title">
    <div className="journey-heading"><div><span className="eyebrow">{j.evidence_mode === 'task-evidence' ? 'SIMULATED INVESTIGATION / SHARED TASK EVIDENCE' : 'SIMULATED JOURNEY / NO INFERENCE REQUIRED'}</span><h2 id="journey-title">Restriction-to-recovery record</h2></div></div>
    <JourneyOutcome state={state} view={view} />
    {j.evidence_mode === 'task-evidence' && !completed && <p className="notice">{j.assessment.eligible ? 'Independent task evidence meets the fixture rules. Commander must review and explicitly approve the simulated correction.' : 'Commander requests an observation; Operator records independent task evidence. Unresolved or conflicting evidence requires clarification or human escalation.'}</p>}
    {presentation !== 'operator' && <ol className="journey-stages" aria-label="Investigation progress">{['Evidence', 'Working diagnosis', 'Human approval', 'Simulated correction', 'Independent verification'].map((label, index) => <li key={label} className={(index < 2 ? j.assessment.eligible || completed : index === 2 ? j.approval_current || completed : index === 3 ? completed : j.recovery.status === 'verified') ? 'stage-done' : ''}><span>{index + 1}</span>{label}</li>)}</ol>}
    {presentation === 'full' && sample && <><div className="journey-metrics"><div><span>Simulated return flow</span><strong>{sample.flow} <small>m3/h</small></strong></div><div><span>Simulated differential pressure</span><strong>{sample.pressure} <small>kPa</small></strong></div><div><span>Simulated valve feedback</span><strong>{sample.valve}<small>%</small></strong></div><div><span>Active simulated alarm</span><strong className="journey-alarm">{sample.alarm ? 'Low return flow' : 'None'}</strong></div></div>
      <p className="caption">Simulated measurement time (UTC): <time dateTime={sample.timestamp}>{sample.timestamp}</time>. This clock advances only with explicit simulation steps.</p></>}
    {release && view === 'operator' && !completed && !state.task && <p className="notice">No observation task is assigned to your identity. Ask Commander and your administrator to arrange an assignment. Untasked simulation reports are unavailable in release mode.</p>}
    {!release && view === 'operator' && !completed && j.evidence_mode !== 'task-evidence' && <section className="section-surface journey-evidence"><h3>Submit simulated field observations</h3><p>Explicit human reports for this local fixture journey. Asset identity is assigned by this task, not established by a photograph. No model analysis or token usage.</p><div className="journey-grid"><form onSubmit={e => { e.preventDefault(); void reportPressure(); }}><h4>F-17 / Local differential pressure</h4><details><summary>Inspect the committed synthetic panel</summary><img src={panelA} alt="Committed synthetic differential-pressure indicator for manual transcription" /><p>Origin: committed synthetic fixture panel-a; your entry remains a simulated human report.</p></details><label>Readability / access<select value={pressureStatus} onChange={e => setPressureStatus(e.target.value)} disabled={disabled}>{['readable', 'unreadable', 'cannot-access', 'wrong-equipment'].map(status => <option key={status}>{status}</option>)}</select></label><label>Local reading (kPa)<input type="number" min="0" max="1000" step="any" value={pressure} disabled={disabled || pressureStatus !== 'readable'} onChange={e => setPressure(e.target.value)} /></label><button className="button secondary" disabled={disabled}>Record local pressure report</button></form>
      <form onSubmit={e => { e.preventDefault(); if (position) void act('observe', { asset_id: 'V-08', status: position, reading: null }, `position-${position}`); }}><h4>V-08 / Position observation only</h4><p>For this rehearsal, report the position you are simulating. No movement is requested and no image verification is claimed.</p><label>Human-reported position<select value={position} onChange={e => setPosition(e.target.value)} disabled={disabled}><option value="">Choose a report</option>{['intermediate', 'open', 'closed', 'cannot determine', 'cannot-access', 'wrong-equipment'].map(value => <option key={value}>{value}</option>)}</select></label><button className="button secondary" disabled={disabled || !position}>Record valve position report</button></form></div></section>}
    {!completed && <div className="journey-grid">
      {(presentation !== 'operator' || (j.approval_current && j.approval_id)) && <section className="section-surface journey-action"><span className="eyebrow">HUMAN-APPROVED SIMULATION</span><h3>Simulate F-17 filter replacement</h3>
        <p>{j.approval_current ? 'Current evidence revision approved. Operator can complete the simulation.' : j.approval_id ? 'Previous approval is stale. Review the current evidence again.' : 'No correction is approved yet.'}</p>
      {view === 'commander' && !completed && <><label className="journey-consent"><input type="checkbox" checked={consent === revision} disabled={disabled || !!blocker} onChange={e => setConsent(e.target.checked ? revision : null)} />I approve only this simulated replacement against evidence revision {revision}.</label><button className="button primary" disabled={disabled || !canApprove(j, revision, consent)} aria-describedby="approval-reason" onClick={() => void act('approve', { action_id: j.action_id, decision: 'approve' })}>Approve simulated correction</button><p className="caption" id="approval-reason">{blocker ?? 'Review the evidence and tick the approval statement first.'}</p><button className="text-button" disabled={disabled} onClick={() => void act('approve', { action_id: j.action_id, decision: 'decline' }, 'decline')}>Decline / revoke approval</button></>}
      {view === 'operator' && !completed && <><button className="button primary" disabled={disabled || !canExecute(j)} onClick={() => void act('execute', { approval_id: j.approval_id })}>Complete simulated filter replacement</button><p className="caption">{j.approval_current ? 'Records simulated completion and applies only the local simulator transition. Recovery is checked separately.' : 'Commander must approve the current evidence revision first.'}</p></>}
      </section>}
      {presentation !== 'operator' && <section className="section-surface journey-assessment"><span className="eyebrow">DETERMINISTIC WORKING DIAGNOSIS / NOT MODEL OUTPUT</span><h3>{j.assessment.working_diagnosis || 'Evidence is incomplete or disputed.'}</h3>
        {j.assessment.blockers.length ? <ul className="journey-blockers">{j.assessment.blockers.map(code => <li key={code}>{code.replaceAll('_', ' ')}</li>)}</ul> : <p className="journey-success">Required observations corroborate this synthetic scenario. Cause remains provisional.</p>}
      </section>}</div>}
    {completed && !terminal && <section className="section-surface journey-progress">{verification}{presentation === 'operator' ? <p>Completion acknowledged. Commander collects the independent verification samples.</p> : advance}</section>}
    <p role="status" className="caption">{message}</p>
    {includeRecord && <JourneyRecord journey={j} completed={completed} />}
    {presentation !== 'operator' && <details className="section-surface journey-rules"><summary>Working diagnosis, competing explanations and fixture rules</summary>
      <p>Assessment source: {j.assessment.source}. {completed ? 'Pre-action evidence supported the recorded correction; this does not prove root cause.' : j.assessment.working_diagnosis ?? 'The required evidence is not yet sufficient.'}</p>
      <ul>{j.assessment.alternatives.map(text => <li key={text}>{text}</li>)}</ul>
      <p>Pre-action evidence freshness: at most {j.policy.freshness_seconds} simulated seconds. Pressure {j.policy.restriction_pressure_kpa.join(' to ')} kPa, local/telemetry agreement +/-{j.policy.pressure_agreement_kpa} kPa; flow {j.policy.restricted_flow_m3h.join(' to ')} m3/h. V-08 must be reported intermediate, with feedback {j.policy.valve_feedback_percent.join(' to ')}%.</p>
      <p>Recovery requires {j.policy.minimum_samples} fresh, consecutive post-action samples spanning {j.policy.window_seconds} simulated seconds: flow {j.policy.recovery_flow_m3h.join(' to ')} m3/h, pressure {j.policy.recovery_pressure_kpa.join(' to ')} kPa, valve feedback {j.policy.valve_feedback_percent.join(' to ')}%, no active alarms.</p>
      <p>All thresholds are fixture-specific constraints, not industrial operating limits. Conflicting or inaccessible reports remain unresolved. A photograph alone does not establish asset identity.</p>
      {terminal && verification}
    </details>}
    {presentation !== 'operator' && !(completed && !terminal) && <details className="section-surface journey-clock-details"><summary>{terminal ? 'Continue simulation (optional)' : 'Simulation clock controls (optional)'}</summary><p>{terminal ? 'No further action is required for the completed walkthrough. Additional samples may change the verification result.' : 'Advancing time can make evidence or approval stale. Submit observations and approve before executing the correction.'}</p>{advance}</details>}
  </section>;
}
