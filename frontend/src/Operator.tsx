import { useState } from 'react';
import { type Action, type Demo, type Evidence, type Outcome, outcomeLabels } from './demo';
import { Icon } from './Icon';
import panelA from '../../fixtures/image-evidence/panel-a.png';
import panelB from '../../fixtures/image-evidence/panel-b.png';

export function Operator({ demo, dispatch, goCommander, inspect }: { demo: Demo; dispatch: (action: Action) => void; goCommander: () => void; inspect: (evidence: Evidence) => void }) {
  const [fixture, setFixture] = useState<'a' | 'b' | null>(null);
  const [response, setResponse] = useState<Outcome | null>(null);
  const [note, setNote] = useState('');
  const [error, setError] = useState('');
  const latest = demo.evidence.at(-1);
  function submit() {
    if (!response && !fixture) { setError('Choose a synthetic image or tell us why the observation cannot be made.'); return; }
    dispatch({ type: 'submit', outcome: response ?? (fixture === 'a' ? 'readable' : 'unreadable'), fixture: response ? undefined : fixture ?? undefined, note });
    setError('');
  }
  return <main className="operator-layout" id="main-content">
    <div className="operator-intro"><span className="eyebrow">OPERATOR WORKSPACE / SAMPLE TASK</span><h1>Bring the field into focus.</h1><p>One observation. A clearer next step.</p></div>
    {!demo.started ? <section className="operator-task section-surface empty-task"><span className="large-symbol"><Icon name="phone" size={36} /></span><h2>No task assigned yet</h2><p>Start the demo incident in Commander to receive an observation request.</p><button className="button primary" onClick={goCommander}>Go to commander <Icon name="arrow" /></button></section>
      : !demo.waiting && latest ? <section className="operator-task section-surface submitted-task"><span className="large-symbol"><Icon name="check" size={36} /></span><span className="eyebrow">RESPONSE RECORDED LOCALLY</span><h2>{outcomeLabels[latest.outcome]}</h2><p>{latest.outcome === 'readable' ? 'The synthetic observation is available in the commander record. The cause is still unverified.' : 'No reading was invented. The commander record now shows the evidence gap.'}</p><button className="button secondary wide" onClick={() => inspect(latest)}>Inspect recorded evidence <Icon name="eye" /></button><button className="button primary wide" onClick={goCommander}>Back to commander <Icon name="arrow" /></button><p className="caption">Same browser only · no cloud or cross-device synchronization</p></section>
      : <section className="operator-task section-surface"><div className="task-topline"><span className="pill amber">Observation requested</span><span className="quiet-label">TASK 01</span></div>
        <div className="task-equipment"><span className="equipment-tag large">F-17</span><div><span className="eyebrow">ASSIGNED EQUIPMENT</span><h2>Return-line filter</h2><p>Cooling loop · local DP indicator</p></div></div>
        <h3>Read the differential-pressure indicator.</h3><p>Check the assigned location, then capture a readable display and unit. If the observation cannot be made, tell the commander why.</p>
        <details className="rationale"><summary>Why this task?</summary><p>The sample flow is falling while differential pressure rises. A local reading helps compare telemetry with field evidence before choosing between restriction, sensor discrepancy, and valve mismatch. It does not establish a diagnosis.</p></details>
        <fieldset className="fixture-picker"><legend>Choose local sample evidence</legend><p className="caption">Committed synthetic fixtures · no camera or upload connection</p><div className="fixture-options">{(['a', 'b'] as const).map(choice => <label className={`fixture-option ${fixture === choice && !response ? 'chosen' : ''}`} key={choice}><input type="radio" name="fixture" checked={fixture === choice && !response} onChange={() => { setFixture(choice); setResponse(null); setError(''); }} /><img src={choice === 'a' ? panelA : panelB} alt={choice === 'a' ? 'Clear synthetic digital instrument' : 'Synthetic instrument with fully obscured display'} /><span>{choice === 'a' ? 'Clear display' : 'Obscured display'}</span></label>)}</div></fieldset>
        <div className="response-alternatives"><span className="eyebrow">UNABLE TO COMPLETE?</span><div>{(['cannot-access', 'wrong-equipment', 'unreadable'] as const).map(value => <button key={value} aria-pressed={response === value} className={`response-button ${response === value ? 'chosen' : ''}`} onClick={() => { setResponse(value); setFixture(null); setError(''); }}>{outcomeLabels[value].replace(' evidence', '')}</button>)}</div>{response && <p className="response-explanation" role="status">{response === 'cannot-access' ? 'Access blocked. No image or reading will be recorded.' : response === 'wrong-equipment' ? 'Equipment identity disputed. This will not be treated as evidence for F-17.' : 'Reading unknown. No number or unit will be recorded.'}</p>}</div>
        <label className="note-label">Observation note <span className="quiet-label">optional</span><textarea value={note} onChange={event => setNote(event.target.value)} maxLength={280} placeholder="Add context for the commander…" rows={3} /></label>
        {error && <p className="form-error" role="alert">{error}</p>}
        <button className="button primary wide" onClick={submit}>{response ? 'Send response' : 'Submit observation'} <Icon name="arrow" /></button><p className="caption">Records a deterministic demo result in this browser. Live AI is not connected.</p>
      </section>}
  </main>;
}
