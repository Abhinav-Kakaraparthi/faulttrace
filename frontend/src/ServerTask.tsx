import { useRef, useState } from 'react';
import { type ServerState } from './api';
import panelA from '../../fixtures/image-evidence/panel-a.png';
import panelB from '../../fixtures/image-evidence/panel-b.png';

type Mutate = (path: string, body: object | Blob, identity: string, extra?: Record<string, string>) => Promise<boolean>;
export function ServerTask({ state, mutate, disabled }: { state: ServerState; mutate: Mutate; disabled: boolean }) {
  const [selection, setSelection] = useState<'panel-a' | 'panel-b' | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState('');
  const input = useRef<HTMLInputElement>(null);
  const selectionKey = useRef(crypto.randomUUID());
  const task = state.task;
  if (!task) return <section className="operator-task section-surface"><h2>No server task assigned</h2><p>Commander must start a simulated incident first.</p></section>;
  const accepts = ['awaiting', 'needs_evidence'].includes(task.status);
  async function upload() {
    if (!task || (!file && !selection)) { setError('Choose a PNG/JPEG file or a committed synthetic fixture.'); return; }
    try {
      const blob = file ?? await (await fetch(selection === 'panel-a' ? panelA : panelB)).blob();
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
    <div className="task-equipment"><span className="equipment-tag large">F-17</span><div><span className="eyebrow">ASSIGNED BY FIXED SIMULATION WORKFLOW</span><h2>Read local differential pressure</h2><p>Capture the indicator and its unit. Identity is not proven by the image.</p></div></div>
    <details className="rationale"><summary>Why this task?</summary><p>Simulated flow decreased while pressure rose. Compare a local observation to the simulated telemetry. Task creation is fixed, not AI planning; no diagnosis or action is authorized.</p></details>
    <fieldset disabled={disabled || !accepts} className="fixture-picker"><legend>Submit image evidence</legend>
      <label className="file-label">PNG or JPEG · up to 2 MiB<input ref={input} type="file" accept="image/png,image/jpeg" onChange={event => { setFile(event.target.files?.[0] ?? null); setSelection(null); selectionKey.current = crypto.randomUUID(); setError(''); }} /></label>
      <p className="caption">16–2048 pixels per side, at most 1,048,576 pixels. Images are privately stored after metadata removal.</p>
      <div className="fixture-options">{(['panel-a', 'panel-b'] as const).map((id, index) => <label key={id} className={`fixture-option ${selection === id ? 'chosen' : ''}`}><input type="radio" name="connected-fixture" checked={selection === id} onChange={() => { setSelection(id); setFile(null); if (input.current) input.current.value = ''; selectionKey.current = crypto.randomUUID(); setError(''); }} /><img src={index === 0 ? panelA : panelB} alt={index === 0 ? 'Committed clear synthetic fixture' : 'Committed obscured synthetic fixture'} /><span>{id} · synthetic fixture</span></label>)}</div>
      <button className="button primary wide" onClick={() => void upload()}>Submit image — no inference yet</button>
      <div className="response-alternatives"><span className="eyebrow">REPORT WITHOUT AN IMAGE</span><div>{['cannot-access', 'wrong-equipment', 'unreadable'].map(value => <button className="response-button" key={value} onClick={() => report(value)}>Report {value.replaceAll('-', ' ')}</button>)}</div></div>
    </fieldset>
    {!accepts && <p className="caption">Current evidence is on the server. Analyze explicitly below or have Commander request another observation.</p>}
    {error && <p role="alert" className="form-error">{error}</p>}
    <p className="caption">Inference is a separate explicit action. Never upload sensitive field evidence in this local validation workflow.</p>
  </section>;
}
