import { useState } from 'react';
import type { ServerEvidence, ServerState } from './api';
import type { Mutate } from './workspace';
import { reviewablePhotos } from './photoSubmission';

export function HumanObservation({ state, mutate, disabled, inspect }: {
  state: ServerState; mutate: Mutate; disabled: boolean; inspect?: (item: ServerEvidence) => void;
}) {
  // Every answer starts blank. Nothing is initialized from model output.
  const [decision, setDecision] = useState('');
  const [asset, setAsset] = useState('');
  const [type, setType] = useState('');
  const [reading, setReading] = useState('');
  const [unit, setUnit] = useState('');
  const [position, setPosition] = useState('');
  const [photo, setPhoto] = useState('');
  const [independent, setIndependent] = useState(false);
  const [error, setError] = useState('');
  const task = state.task;
  if (!task || state.journey?.evidence_mode !== 'task-evidence') return null;
  const photos = reviewablePhotos(state);
  const legacy = state.evidence.some(e => e.task_id === task.id && e.kind === 'image' && e.analysis?.interpretation && e.analysis.contract !== 'photo-observation-v1');
  const selected = photos.find(e => e.id === photo);
  const numeric = type === 'pressure' || type === 'differential_pressure';
  const closed = state.journey.maintenance_status !== 'not_completed';
  const accepting = ['awaiting', 'needs_evidence', 'observed'].includes(task.status);
  async function submit(event: React.FormEvent) {
    event.preventDefault(); setError('');
    if (!task || !state.incident) return;
    if (decision !== 'independent' && !selected) { setError('Choose an analyzed photograph using the photographic observation contract. Legacy test-display results cannot be confirmed here.'); return; }
    if (numeric && (!reading.trim() || !Number.isFinite(Number(reading)))) {
      setError('Enter your own finite reading and visible unit.'); return;
    }
    await mutate(`/api/tasks/${task.id}/observations`, { revision: state.incident.revision,
      task_revision: task.revision, decision, observed_asset_id: asset,
      measurement_type: type, reading: numeric ? Number(reading) : null,
      unit: numeric ? unit : null, position: type === 'position' ? position : null,
      photo_id: decision === 'independent' ? null : photo, independent },
      `human-observation-${task.id}-${task.revision}`);
  }
  return <form id="independent-observation" tabIndex={-1} className="human-observation" onSubmit={e => void submit(e)}>
    <h3>Record your independent observation</h3>
    <p>Simulation report, not a real equipment action. Enter what you independently observe or are rehearsing. A photo interpretation is an unverified model claim.</p>
    <fieldset disabled={disabled || closed || !accepting}><legend>Human evidence for assigned {task.asset_id}</legend>
      <label>Observation source<select required value={decision} onChange={e => { setDecision(e.target.value); setPhoto(''); }}>
        <option value="">Choose source</option><option value="independent">Independent field report, without a photograph</option>
        <option value="confirm" disabled={!photos.length}>Independently confirm a photographic claim</option><option value="dispute" disabled={!photos.length}>Dispute a photographic claim</option>
      </select></label>
      {legacy && !photos.length && <p className="notice">The stored test-display result uses a legacy contract and cannot be confirmed as photographic evidence. Its history is preserved. Collect a real photograph or report the unresolved task; do not identify equipment from its assignment.</p>}
      {decision && decision !== 'independent' && <><label>Source photograph<select required value={photo} onChange={e => setPhoto(e.target.value)}>
        <option value="">Choose stored photograph</option>{photos.map(e => <option key={e.id} value={e.id}>Assigned {e.asset_id} / {e.created_at}</option>)}
      </select></label>{selected && inspect && <button type="button" className="button secondary" onClick={() => inspect(selected)}>Inspect source photograph</button>}
        {!photos.length && <p>No analyzed photographic claim is ready for review. Upload and explicitly analyze a photograph above, or record an independent field report.</p>}</>}
      <label>Equipment identity you independently observed<select required value={asset} onChange={e => setAsset(e.target.value)}>
        <option value="">Choose observed identity</option>{['F-17','V-08','unknown','other'].map(a => <option key={a}>{a}</option>)}
      </select></label>
      <label>Measurement type you observed<select required value={type} onChange={e => setType(e.target.value)}>
        <option value="">Choose measurement type</option>{['differential_pressure','pressure','position','unknown'].map(t => <option key={t} value={t}>{t.replaceAll('_',' ')}</option>)}
      </select></label>
      {numeric && <div className="human-reading-fields"><label>Your reading<input required type="number" step="any" value={reading} onChange={e => setReading(e.target.value)} placeholder="Enter your observed value" /></label>
        <label>Your observed unit<select required value={unit} onChange={e => setUnit(e.target.value)}><option value="">Choose unit</option>{['Pa','kPa','MPa','bar','psi'].map(u => <option key={u}>{u}</option>)}</select></label></div>}
      {type === 'position' && <label>Your position observation<select required value={position} onChange={e => setPosition(e.target.value)}><option value="">Choose position</option>{['open','intermediate','closed','cannot determine'].map(p => <option key={p}>{p}</option>)}</select></label>}
      <label className="journey-consent"><input type="checkbox" checked={independent} onChange={e => setIndependent(e.target.checked)} />I entered my own observation, including identity and measurement type; assignment and model output are not verification.</label>
      <button className="button primary" disabled={!independent || !decision || !asset || !type || (decision !== 'independent' && !photo)}>Record human observation</button>
    </fieldset>
    <p className="caption">Conflicting, incompatible or stale reports stay in the audit record and block correction. No model value is prefilled. Corrections need Commander approval and independent recovery samples.</p>
    {error && <p role="alert">{error}</p>}
  </form>;
}

export function HumanObservationDetails({ evidence }: { evidence: ServerEvidence }) {
  const human = evidence.human_observation;
  if (!human) return null;
  return <section><h3>Independent human report / {human.decision}</h3>
    <p>Observed identity: {human.observed_asset_id} · type: {human.measurement_type.replaceAll('_',' ')}.</p>
    <p>Original human observation: {human.reading ?? human.position ?? 'unknown'} {human.unit ?? ''}. Source: simulated human report, not image-verified.</p>
    {human.normalized_kpa !== null && <p>Policy comparison: {human.normalized_kpa} kPa, normalized from the independent human report.</p>}
    {!!human.flags.length && <><strong>Unresolved / clarification required</strong><ul>{human.flags.map(flag => <li key={flag}>{flag.replaceAll('_',' ')}</li>)}</ul></>}
    <details><summary>Human report provenance</summary><p>Task {evidence.task_id} · source photo {human.photo_id ?? 'none'}.</p>
      <p>Simulated measurement time: {human.timestamp}. Wall-clock received: {human.received_at}.</p>
      <p>The original model interpretation is preserved separately. This report alone does not authorize correction or establish recovery.</p></details>
  </section>;
}
