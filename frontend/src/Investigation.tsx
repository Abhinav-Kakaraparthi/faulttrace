import { type Demo, type Evidence, outcomeLabels } from './demo';
import { Icon } from './Icon';

export function Investigation({ demo }: { demo: Demo }) {
  const latest = demo.evidence.at(-1);
  return <aside className="investigation section-surface" aria-labelledby="investigation-title">
    <div className="section-heading"><div><span className="eyebrow">INVESTIGATION</span><h2 id="investigation-title">Keep the alternatives open.</h2></div><span className="step-count">3 leads</span></div>
    <p className="muted">Sample explanations, not an AI diagnosis. Evidence narrows the next question.</p>
    <div className="hypothesis"><div className="hypothesis-heading"><span className="number">01</span><strong>Filter restriction</strong><span className="pill amber">Plausible</span></div><p>Lower flow and rising differential pressure could indicate increased resistance.</p><span className="gap">{latest?.outcome === 'readable' ? 'Local sample reading supports elevated pressure; cause remains open.' : 'Gap: independent local pressure reading.'}</span></div>
    <div className="hypothesis"><div className="hypothesis-heading"><span className="number">02</span><strong>Sensor discrepancy</strong></div><p>Telemetry may not match the condition at the instrument.</p><span className="gap">Gap: inspect the indicator and confirm instrument identity.</span></div>
    <div className="hypothesis"><div className="hypothesis-heading"><span className="number">03</span><strong>Valve position mismatch</strong></div><p>Position feedback may differ from the physical position.</p><span className="gap">Gap: physical position has not been observed.</span></div>
    <div className="verification-note"><span className="status-dot" /> Recovery not assessed · No equipment actions</div>
  </aside>;
}

export function ActivityPanel({ demo, inspect }: { demo: Demo; inspect: (evidence: Evidence) => void }) {
  return <section className="activity section-surface" aria-labelledby="activity-title"><div className="section-heading"><div><span className="eyebrow">INVESTIGATION RECORD</span><h2 id="activity-title">Every observation has a source.</h2></div><span className="quiet-label">Oldest first</span></div>
    {!demo.activity.length ? <div className="empty-record"><Icon name="trace" size={30} /><p>No incident activity yet.</p><span>Start the demo to follow the evidence trail.</span></div> : <ol className="timeline">{demo.activity.map((event, index) => <li key={index}><span className="event-index">{String(index + 1).padStart(2, '0')}</span><div><strong>{event.title}</strong><p>{event.detail}</p>{event.evidence && <button className="text-button" onClick={() => inspect(demo.evidence.find(item => item.id === event.evidence)!)}>Inspect evidence <Icon name="eye" size={16} /></button>}</div><span className="quiet-label">Sample</span></li>)}</ol>}
  </section>;
}

export function EvidenceDialog({ evidence, close }: { evidence: Evidence; close: () => void }) {
  return <><div className="dialog-heading"><div><span className="eyebrow">EVIDENCE / {String(evidence.id).padStart(2, '0')}</span><h2>Inspect the source</h2></div><button className="icon-button" aria-label="Close evidence inspection" onClick={close}><Icon name="close" /></button></div>
    <span className={`pill ${evidence.outcome === 'readable' ? 'teal' : 'amber'}`}>{outcomeLabels[evidence.outcome]}</span>
    {evidence.fixture ? <img className="evidence-image" src={evidence.fixture === 'a' ? new URL('../../fixtures/image-evidence/panel-a.png', import.meta.url).href : new URL('../../fixtures/image-evidence/panel-b.png', import.meta.url).href} alt={evidence.fixture === 'a' ? 'Synthetic differential-pressure display showing 180 kPa' : 'Synthetic instrument with the whole reading and unit obscured'} /> : <div className="no-image"><Icon name="eye" size={32} /><p>No image submitted.</p></div>}
    <dl className="evidence-facts"><div><dt>Source</dt><dd>{evidence.fixture ? `Committed synthetic fixture · panel-${evidence.fixture}.png` : 'Human-style response · deterministic demo'}</dd></div><div><dt>Reading</dt><dd>{evidence.outcome === 'readable' ? '180 kPa · sample transcription' : 'Unknown · no numeric reading recorded'}</dd></div><div><dt>Readability</dt><dd>{evidence.outcome === 'readable' ? 'Readable synthetic display' : evidence.outcome === 'unreadable' ? 'Unreadable / operator-reported' : 'Not observed'}</dd></div><div><dt>Equipment</dt><dd>{evidence.outcome === 'wrong-equipment' ? 'Disputed · not assigned to F-17' : 'F-17 · task-assigned, not image-verified'}</dd></div></dl>
    {evidence.note && <p className="operator-note">Operator note: {evidence.note}</p>}
    <div className="notice">Fixture origin: generated locally for this demo. No image model has analyzed this submission. It proves neither asset identity nor completed work.</div>
  </>;
}
