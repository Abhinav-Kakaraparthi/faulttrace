import { useId } from 'react';
import { type ServerState } from './api';
import { escalatedWithoutTask, planningBlocker } from './planningPolicy';
import { HTTPDiagnostics } from './HTTPDiagnostics';

export function PlannerPanel({ state, disabled, choose, open, inspect, historyOnly = false }: {
  state: ServerState; disabled: boolean; choose: () => void; open: () => void; inspect?: (item: ServerState['evidence'][number]) => void; historyOnly?: boolean;
}) {
  const task = state.task;
  const escalated = escalatedWithoutTask(state);
  const accepted = state.planning.filter(p => ['accepted', 'escalated'].includes(p.status) && p.proposal).at(-1);
  const reasonId = useId();
  const pending = state.planning.some(item => item.status === 'pending');
  const blocker = planningBlocker(state);
  const unavailable = disabled || blocker !== null;
  return <section className="observation-task section-surface planner-panel">
    {historyOnly ? <h2>Observation planning history</h2> : <>
    <span className="eyebrow">OBSERVATION PLANNING · SIMULATED INCIDENT</span>
    <h2>{escalated ? 'Human investigation requested' : task ? `${task.asset_id} · Observation` : 'Choose the next observation'}</h2>
    {task ? <><p>{task.instruction}</p><span className="pill amber">{task.status} · revision {task.revision}</span>
      <p className="caption">Source: {task.creation_source}</p>
      <details className="rationale"><summary>Why this task?</summary><p>{task.explanation}</p><p>No equipment action or recovery is authorized.</p></details>
      <button className="button secondary wide" onClick={open}>Open operator task</button></> : escalated ? <p>NVIDIA requested human review, so no Operator observation task was created. Keep this incident for human investigation and review the cited evidence below. This is not a diagnosis or proof that every observation was tried.</p> : <p>No task is assigned automatically. NVIDIA may propose an observation; application policy creates the task.</p>}
    {!escalated && <button className="button primary wide repeat-observation planner-choose" disabled={unavailable} aria-describedby={reasonId} onClick={choose}>{pending ? 'Planning request pending' : 'Choose next observation'}</button>}
    <p id={reasonId} className="caption" role="status">{blocker ?? (disabled ? 'Server unavailable or another request is in progress.' : state.test_output ? 'One scripted offline provider-double call; no live AI.' : 'One explicit NVIDIA text request. No automatic retry.')} {state.planning_remaining} of 4 planning turns remain.</p>
    </>}
    {accepted?.proposal && <div className="accepted-references"><h3>Latest accepted proposal cites</h3>
      <ul>{accepted.proposal.evidence_refs.map(ref => {
        const evidence = state.evidence.find(e => `evidence-${e.id}` === ref);
        return <li key={ref}>{evidence && inspect ? <button className="button secondary" onClick={() => inspect(evidence)}>Inspect cited {evidence.kind === 'image' ? 'photograph' : 'human report'} · assigned {evidence.asset_id}</button> : <span>{ref}</span>}</li>;
      })}</ul><p className="caption">Citations support the observation choice; they do not validate a measurement or authorize correction.</p></div>}
    {historyOnly && !state.planning.length && <p>No NVIDIA planning attempts in this run. The simulated journey used human reports and deterministic policy.</p>}
    {!!state.planning.length && <details className="rationale"><summary>Planning history ({state.planning.length})</summary><ol className="planning-history">{state.planning.map(item => <li key={item.id}>
      <strong>{item.status === 'escalated' ? 'Human investigation requested' : item.status} · context {item.context_revision}</strong>
      {item.proposal && <p>{item.proposal.kind} / {item.proposal.asset_id}<br />{item.explanation}<br />References: {item.proposal.evidence_refs.join(', ')}</p>}
      {item.error && <p>Diagnostic: {item.error}</p>}
      {item.receipt && <HTTPDiagnostics receipt={item.receipt} />}
      {item.receipt && <p>Known input / output / total: {item.receipt.token_usage?.prompt_tokens ?? 'unknown'} / {item.receipt.token_usage?.completion_tokens ?? 'unknown'} / {item.receipt.token_usage?.total_tokens ?? 'unknown'}. Usage {item.receipt.usage_status}; ledger {item.accounting}.</p>}
      <span className="caption">Attempt {item.id}{item.task_id ? ` · Task ${item.task_id}` : ''}</span>
    </li>)}</ol></details>}
  </section>;
}
