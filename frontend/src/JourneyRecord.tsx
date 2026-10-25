import type { JourneyState } from './journeyState';

export function measurement(value: unknown): string {
  return typeof value === 'number' && Number.isFinite(value) ? String(value) : 'Unknown';
}
export function referenceText(value: unknown): string {
  return typeof value === 'string' && value.trim() ? value : 'Reference unavailable';
}

export function JourneyRecord({ journey: j, completed }: { journey: JourneyState; completed: boolean }) {
  const refs = completed ? j.approved_evidence_refs : j.assessment.evidence_refs;
  const known = new Set([...j.samples.map(s => s.id), ...j.observations.map(o => o.id)]);
  return <section className="section-surface journey-record" aria-labelledby="journey-record-title">
    <h3 id="journey-record-title">Journey evidence record</h3>
    <p>{j.observations.length} simulated human observations and {j.samples.length} simulator measurements. These are separate from image uploads and NVIDIA planner-task submissions.</p>
    {!j.observations.length ? <p>No journey observations yet. Telemetry alone cannot authorize correction.</p> :
      <ul className="journey-observations">{j.observations.map((o, i) => <li key={o.id || i}>
        <strong>{o.asset_id} / {o.status}{o.reading !== null ? ` / ${measurement(o.reading)} ${o.unit ?? 'unit unknown'}` : ''}</strong>
        <span>Simulated human report; not image-verified.</span>
        <details><summary>Measurement time, source and reference</summary>
          <p>Simulated measurement time (UTC): <time dateTime={o.timestamp}>{o.timestamp || 'Unknown'}</time></p>
          <p>Source: {o.origin || 'Unknown'}</p><code>{referenceText(o.id)}</code>
        </details>
      </li>)}</ul>}
    <details className="journey-reference-details"><summary>{completed ? 'Approval evidence references' : 'Assessment evidence references'} ({refs.length})</summary>
      {!refs.length ? <p>No references recorded.</p> : <ol className="journey-refs">{refs.map((ref, i) => <li key={`${ref}-${i}`}><code>{referenceText(ref)}</code>{!known.has(ref) && <span>Reference not present in this snapshot; no link is available.</span>}</li>)}</ol>}
      <p>References identify the stored records; no external evidence link is implied.</p>
    </details>
    <details><summary>Telemetry measurements and recovery references ({j.samples.length})</summary>
      <div className="journey-table" tabIndex={0} role="region" aria-label="Scrollable simulated telemetry table">
        <table><caption>Simulated measurement times (UTC), not wall-clock audit times. Every row is a stored sample.</caption>
          <thead><tr><th scope="col">Simulation time (UTC)</th><th scope="col">Flow m3/h</th><th scope="col">DP kPa</th><th scope="col">Valve %</th><th scope="col">Alarm</th><th scope="col">Stored reference</th><th scope="col">Verification scope</th></tr></thead>
          <tbody>{j.samples.map((s, i) => <tr key={s.id || i}>
            <td><time dateTime={s.timestamp}>{s.timestamp || 'Unknown'}</time></td>
            <td>{measurement(s.flow)}</td><td>{measurement(s.pressure)}</td><td>{measurement(s.valve)}</td>
            <td>{s.alarm === null ? 'None' : s.alarm || 'Unknown'}</td><td><code>{referenceText(s.id)}</code></td>
            <td>{j.recovery.sample_refs.includes(s.id) ? 'Post-correction verification sample' : 'Pre-correction / outside verification'}</td>
          </tr>)}</tbody>
        </table>{!j.samples.length && <p>No stored telemetry samples.</p>}
      </div>
    </details>
  </section>;
}
