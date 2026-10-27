import { type ServerEvidence as Evidence, type ServerState } from './api';
import { EvidencePhoto } from './EvidencePhoto';
import { evidenceStatus, evidenceTimestamp } from './evidencePresentation';
import { PhotoPlanningAssessment } from './PhotoPlanning';
import { HTTPDiagnostics } from './HTTPDiagnostics';
export { statusLabel } from './evidencePresentation';
export { ServerEvidenceDetails } from './EvidenceDetails';

export function ServerEvidenceList({ state, inspect, analyze, disabled, allowAnalysis = true }: {
  state: ServerState; inspect: (item: Evidence) => void; analyze: (item: Evidence) => void; disabled: boolean; allowAnalysis?: boolean;
}) {
  const latestPhoto = state.evidence.filter(e => e.kind === 'image' && e.task_id === state.task?.id).at(-1)?.id;
  const latest = state.evidence.at(-1)?.id;
  return <section className="section-surface connected-evidence"><h2>{state.journey?.evidence_mode === 'task-evidence' ? 'Shared task evidence and independent reports' : state.journey ? 'Image and planner-task evidence' : 'Server evidence record'}</h2>
    {!state.evidence.length && <p className="muted">{state.journey ? `No image or planner-task submissions in this run. The ${state.journey.observations.length} simulated journey observations are recorded in Journey evidence record.` : 'No evidence submitted for the observation task. Both tabs read the same server task.'}</p>}
    {state.evidence.map(item => <article key={item.id} data-evidence-id={item.id} className="server-evidence-item compact-evidence-row">
      {item.kind === 'image' ? <EvidencePhoto evidence={item} compact /> : <span className="report-thumbnail" aria-hidden="true">Human report</span>}
      <div className="evidence-row-summary"><h3>Assigned asset: {item.asset_id}</h3>
        <span className={`pill ${item.status === 'accepted' ? 'teal' : 'amber'}`}>{evidenceStatus(item)}</span>
        <time dateTime={item.created_at}>{evidenceTimestamp(item.created_at)} · wall-clock</time>
        {item.photo_assessment && <PhotoPlanningAssessment value={item.photo_assessment} />}
        {item.kind === 'report' && <p>Human report / {item.human_observation ? `${item.human_observation.decision}: ${item.human_observation.reading ?? item.human_observation.position ?? 'unknown'} ${item.human_observation.unit ?? ''}` : item.report}</p>}
      </div>
      <button className="button secondary inspect-evidence" aria-label={`Inspect evidence for ${item.asset_id}, ${evidenceTimestamp(item.created_at)}`} onClick={() => inspect(item)}>Inspect evidence</button>
      {allowAnalysis && item.task_id === state.task?.id && !item.analysis && ((item.id === latest && item.status === 'pending') || (item.kind === 'image' && item.status === 'collected' && item.id === latestPhoto)) && <details className="evidence-row-options"><summary>Analysis options</summary>
        {item.status === 'pending' ? <button className="button secondary" disabled={disabled || !state.inference_enabled} onClick={() => analyze(item)}>Analyze image</button>
          : <button className="button secondary" disabled={disabled || !state.inference_enabled || state.photo_analysis?.contract !== 'photo-observation-v1' || !['awaiting','needs_evidence','observed'].includes(state.task?.status ?? '')} onClick={() => analyze(item)}>Analyze photographic observation</button>}
        <p className="caption">{!state.inference_enabled && 'Inference is disabled. '}{item.status === 'collected' && state.photo_analysis?.contract !== 'photo-observation-v1' ? 'Photographic analysis requires an updated backend.' : state.test_output ? 'Offline provider double only; no live AI. Interpretation does not complete a measurement task.' : 'One explicit NVIDIA request; no automatic retry. Interpretation does not complete the task or authorize correction.'}</p>
      </details>}
      {item.analysis?.receipt && <details className="evidence-row-options"><summary>Analysis status &amp; accounting</summary><HTTPDiagnostics receipt={item.analysis.receipt} />
        <p>Known tokens: input {item.analysis.receipt.token_usage?.prompt_tokens ?? 'unknown'} / output {item.analysis.receipt.token_usage?.completion_tokens ?? 'unknown'} / total {item.analysis.receipt.token_usage?.total_tokens ?? 'unknown'} · Usage {item.analysis.receipt.usage_status} · Ledger {item.analysis.accounting}</p>
        {item.analysis.error && <p>Diagnostic: {item.analysis.error}</p>}
        {item.analysis.status === 'uncertain' && <p>Interrupted analysis is not retried. Any retained interpretation requires review.</p>}
      </details>}
    </article>)}
  </section>;
}
