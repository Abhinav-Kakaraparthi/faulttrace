import { useRef, useState } from 'react';
import { type ServerState } from './api';
import panelA from '../../fixtures/image-evidence/panel-a.png';
import panelB from '../../fixtures/image-evidence/panel-b.png';

import type { Mutate } from './workspace';
import { HumanObservation } from './HumanObservation';
import { PhotoCapture } from './PhotoCapture';

export function ServerTask({ state, mutate, disabled, inspect }: { state: ServerState; mutate: Mutate; disabled: boolean; inspect?: (item: ServerState['evidence'][number]) => void }) {
  const [selection, setSelection] = useState<'panel-a' | 'panel-b' | null>(null);
  const [error, setError] = useState('');
  const selectionKey = useRef(crypto.randomUUID());
  const task = state.task;
  if (!task) return <section className="operator-task section-surface"><h2>No server task assigned</h2><p>Waiting for Commander to assign an observation. No task is assigned automatically.</p></section>;
  const accepts = ['awaiting', 'needs_evidence'].includes(task.status);
  const unified = state.journey?.evidence_mode === 'task-evidence';
  async function upload() {
    if (!task || !selection) { setError('Choose a committed synthetic fixture.'); return; }
    try {
      const blob = await (await fetch(selection === 'panel-a' ? panelA : panelB)).blob();
      if (!['image/png', 'image/jpeg'].includes(blob.type) || blob.size > 2 * 1024 * 1024) {
        setError('PNG/JPEG only, maximum 2 MiB.'); return;
      }
      const headers: Record<string, string> = { 'X-Task-Revision': String(task.revision) };
      if (selection) headers['X-Fixture-Id'] = selection;
      await mutate(`/api/tasks/${task.id}/images`, blob, `upload-${task.id}-${task.revision}-${selectionKey.current}`, headers);
    } catch { setError('Local image could not be read. No analysis was requested.'); }
  }
  function report(value: string) {
    if (task) void mutate(`/api/tasks/${task.id}/reports`, { revision: task.revision, report: value }, `report-${task.id}-${task.revision}-${value}`);
  }
  return <section className="operator-task section-surface"><div className="task-topline"><span className="pill amber">{task.status.replaceAll('_', ' ')} · revision {task.revision}</span><span className="quiet-label">Server task</span></div>
    <div className="task-equipment"><span className="equipment-tag large">{task.asset_id}</span><div><span className="eyebrow">{task.creation_source.startsWith('TEST-CREATED') ? 'Test-created · not AI-generated' : task.creation_source}</span><h2>{task.asset_id === 'V-08' ? 'Observe valve position only' : 'Read local differential pressure'}</h2><p>{task.instruction}</p></div></div>
    <details className="rationale"><summary>Why this task?</summary><p>{task.explanation} No diagnosis or action is authorized.</p><p>Source: {task.creation_source}. Task revision {task.revision}.</p></details>
    <PhotoCapture asset={task.asset_id} disabled={disabled || !accepts} supported={state.photo_collection?.version === 1 && state.photo_collection.assets.includes(task.asset_id)} upload={(blob, identity, progress) => mutate(`/api/tasks/${task.id}/images`, blob, `photo-${task.id}-${task.revision}-${identity}`, { 'X-Task-Revision': String(task.revision), 'X-Evidence-Purpose': 'reference-photo' }, progress)} />
    {unified && <HumanObservation state={state} mutate={mutate} disabled={disabled} inspect={inspect} />}
    {task.asset_id === 'V-08' ? <fieldset disabled={disabled || !accepts} className="fixture-picker"><legend>V-08 position · human report</legend><p>Visible position only; do not move the valve.</p><div className="response-alternatives">{(unified ? ['cannot-access', 'wrong-equipment'] : ['open', 'intermediate', 'closed', 'cannot determine', 'cannot-access', 'wrong-equipment']).map(value => <button className="response-button" key={value} onClick={() => report(value)}>Report {value === 'cannot determine' ? 'cannot determine / unreadable position' : value}</button>)}</div></fieldset> : <><fieldset disabled={disabled || !accepts} className="observation-alternatives"><legend>Cannot supply a photograph?</legend><div className="response-alternatives">{['cannot-access', 'wrong-equipment', 'unreadable'].map(value => <button className="response-button" key={value} onClick={() => report(value)}>Report {value.replaceAll('-', ' ')}</button>)}</div></fieldset><details className="fixture-development"><summary>Development / test: synthetic fixtures</summary><fieldset disabled={disabled || !accepts} className="fixture-picker"><legend>Synthetic DP-display regression fixtures</legend>
      <p className="caption">Synthetic regression fixtures only; not photographs or proof of equipment identity. Explicit DP-display analysis remains separate.</p>
      <div className="fixture-options">{(['panel-a', 'panel-b'] as const).map((id, index) => <label key={id} className={`fixture-option ${selection === id ? 'chosen' : ''}`}><input type="radio" name="connected-fixture" checked={selection === id} onChange={() => { setSelection(id); selectionKey.current = crypto.randomUUID(); setError(''); }} /><img src={index === 0 ? panelA : panelB} alt={index === 0 ? 'Committed clear synthetic fixture' : 'Committed obscured synthetic fixture'} /><span>{id} · synthetic fixture</span></label>)}</div>
      <button className="button primary wide" onClick={() => void upload()}>Submit image — no inference yet</button>
    </fieldset></details></>}
    {!accepts && <p className="caption">Current evidence is on the server. Analyze explicitly below or have Commander request another observation.</p>}
    {error && <p role="alert" className="form-error">{error}</p>}
  </section>;
}
