import { useId } from 'react';
import { type ServerState } from './api';
import { planningBlocker } from './planningPolicy';

export function PlannerPanel({ state, disabled, choose, open }: {
  state: ServerState; disabled: boolean; choose: () => void; open: () => void;
}) {
  const task = state.task;
  const reasonId = useId();
  const pending = state.planning.some(item => item.status === 'pending');
  const blocker = planningBlocker(state);
  const unavailable = disabled || blocker !== null;
  return <section className="observation-task section-surface planner-panel">
    <span className="eyebrow">OBSERVATION PLANNING · SIMULATED INCIDENT</span>
    <h2>{task ? `${task.asset_id} · Observation` : 'Choose the next observation'}</h2>
    {task ? <><p>{task.instruction}</p><span className="pill amber">{task.status} · revision {task.revision}</span>
      <p className="caption">Source: {task.creation_source}</p>
      <details className="rationale"><summary>Why this task?</summary><p>{task.explanation}</p><p>No equipment action or recovery is authorized.</p></details>
      <button className="button secondary wide" onClick={open}>Open operator task</button></> : <p>No task is assigned automatically. NVIDIA may propose an observation; application policy creates the task.</p>}
    <button className="button primary wide repeat-observation planner-choose" disabled={unavailable} aria-describedby={reasonId} onClick={choose}>{pending ? 'Planning request pending' : 'Choose next observation'}</button>
    <p id={reasonId} className="caption" role="status">{blocker ?? (disabled ? 'Server unavailable or another request is in progress.' : 'One explicit NVIDIA text request. No automatic retry.')} {state.planning_remaining} of 4 planning turns remain.</p>
    {!!state.planning.length && <details className="rationale"><summary>Planning history ({state.planning.length})</summary><ol className="planning-history">{state.planning.map(item => <li key={item.id}>
      <strong>{item.status === 'escalated' ? 'Human investigation requested' : item.status} · context {item.context_revision}</strong>
      {item.proposal && <p>{item.proposal.kind} / {item.proposal.asset_id}<br />{item.explanation}<br />References: {item.proposal.evidence_refs.join(', ')}</p>}
      {item.error && <p>Diagnostic: {item.error}</p>}
      {item.receipt && <p>Known input / output / total: {item.receipt.token_usage?.prompt_tokens ?? 'unknown'} / {item.receipt.token_usage?.completion_tokens ?? 'unknown'} / {item.receipt.token_usage?.total_tokens ?? 'unknown'}. Usage {item.receipt.usage_status}; ledger {item.accounting}.</p>}
      <span className="caption">Attempt {item.id}{item.task_id ? ` · Task ${item.task_id}` : ''}</span>
    </li>)}</ol></details>}
  </section>;
}
