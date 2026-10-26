import { type ServerEvidence as Evidence, type ServerState } from './api';
import { EvidencePhoto } from './EvidencePhoto';
import { HTTPDiagnostics } from './HTTPDiagnostics';

export const statusLabel: Record<string, string> = {
  collected: 'Photograph collected / not analyzed',
  pending: 'Image accepted · not analyzed', accepted: 'Accepted model interpretation',
  unreadable: 'Unreadable · clearer evidence needed', refused: 'Operator refusal',
  failed: 'Analysis failed · no automatic retry', stale: 'Stale evidence · superseded task',
  uncertain: 'Uncertain · analysis interrupted',
};

function evidenceStatus(item: Evidence) {
  if (item.kind === 'report' && item.status === 'accepted') return 'Accepted human report · not image-verified';
  return item.analysis?.status === 'pending' ? 'Analysis pending · no reading yet' : statusLabel[item.status] ?? item.status;
}

export function ServerEvidenceList({ state, inspect, analyze, disabled, allowAnalysis = true }: {
  state: ServerState; inspect: (item: Evidence) => void; analyze: (item: Evidence) => void; disabled: boolean; allowAnalysis?: boolean;
}) {
  const latest = state.evidence.at(-1)?.id;
  return <section className="section-surface connected-evidence"><h2>{state.journey ? 'Image and planner-task evidence' : 'Server evidence record'}</h2>
    {!state.evidence.length && <p className="muted">{state.journey ? `No image or planner-task submissions in this run. The ${state.journey.observations.length} simulated journey observations are recorded in Journey evidence record.` : 'No evidence submitted for the observation task. Both tabs read the same server task.'}</p>}
    {state.evidence.map(item => <article key={item.id} className="server-evidence-item">
      <span className={`pill ${item.status === 'accepted' ? 'teal' : 'amber'}`}>
        {evidenceStatus(item)}
      </span><h3>{item.kind === 'image' ? item.status === 'collected' ? 'Collection-only photograph' : 'Image observation' : `Human report: ${item.report}`}</h3>
      <EvidencePhoto evidence={item} compact />
      <p>Assigned asset: {item.asset_id}. Image-supported identity: not assessed; assignment is not identification.</p>
      {item.status === 'collected' && <p className="notice">Collection only: no instrument reading, valve interpretation or inference requested. Ordinary pressure is not differential pressure; a handle photograph does not prove internal valve condition.</p>}
      {item.kind === 'report' && <p>Human report / {item.report}. This is not a NVIDIA interpretation.</p>}
      <p>Source: {item.origin}{item.fixture_id ? ` / ${item.fixture_id}` : ''} · Task revision {item.submitted_revision}</p>
      {item.analysis?.interpretation && <p className="model-reading">NVIDIA interpretation (existing DP-display contract only): {item.analysis.interpretation.readability === 'readable' ? `${item.analysis.interpretation.reading} ${item.analysis.interpretation.unit}` : 'unreadable — reading and unit unknown'}</p>}
      {item.analysis?.interpretation && <p className="notice">The current model contract does not verify gauge type or photographed identity. Do not use this as differential pressure without independent confirmation that the instrument measures differential pressure; units alone do not establish that.</p>}
      {item.analysis?.status === 'uncertain' && <p className="amber-text">Interrupted analysis is not retried. Any retained interpretation requires review.</p>}
      {item.analysis?.receipt && <HTTPDiagnostics receipt={item.analysis.receipt} />}
      {item.analysis?.receipt && <p>Known tokens: input {item.analysis.receipt.token_usage?.prompt_tokens ?? 'unknown'} / output {item.analysis.receipt.token_usage?.completion_tokens ?? 'unknown'} / total {item.analysis.receipt.token_usage?.total_tokens ?? 'unknown'} · Usage {item.analysis.receipt.usage_status} · Ledger {item.analysis.accounting}</p>}
      <div className="server-evidence-actions"><button className="button secondary" onClick={() => inspect(item)}>Inspect evidence</button>
        {allowAnalysis && item.task_id === state.task?.id && item.id === latest && item.status === 'pending' && !item.analysis && <button className="button primary" disabled={disabled || !state.inference_enabled} onClick={() => analyze(item)}>Analyze image</button>}
      </div>
      {item.id === latest && item.status === 'pending' && !state.inference_enabled && <p className="caption">Inference disabled by default. Backend must be explicitly started with FAULTTRACE_ALLOW_INFERENCE=1.</p>}
    </article>)}
  </section>;
}

export function ServerEvidenceDetails({ evidence }: { evidence: Evidence }) {
  const receipt = evidence.analysis?.receipt;
  return <><span className="pill amber">{evidenceStatus(evidence)}</span>
    {evidence.kind === 'image' ? <EvidencePhoto evidence={evidence} /> : <p>Human report only: {evidence.report}. No image or image-based identity verification supplied.</p>}
    <p className="notice">Assigned asset: {evidence.asset_id}. Image-supported identity: not assessed. Record visible tags as seen; do not rename a different tagged asset to match the assignment.</p>
    {evidence.status === 'collected' && <p>Collection-only photograph. No pressure reading inferred. Analog gauges and valve interpretation require separate evaluation; a valve handle does not establish internal valve condition.</p>}
    <dl className="evidence-facts">
      <div><dt>Origin</dt><dd>{evidence.origin} {evidence.fixture_id}</dd></div>
      <div><dt>Evidence ID</dt><dd>{evidence.id}</dd></div>
      <div><dt>Task</dt><dd>{evidence.asset_id} · application-assigned, not image-verified</dd></div>
      <div><dt>Human report</dt><dd>{evidence.kind === 'report' ? evidence.report : 'No human report in this image record'}</dd></div>
      <div><dt>Image-supported asset identity</dt><dd>Not assessed by the current contract; assignment does not establish identity.</dd></div>
      <div><dt>NVIDIA readability (if analyzed)</dt><dd>{evidence.analysis?.interpretation?.readability ?? 'Not analyzed'}</dd></div>
      <div><dt>NVIDIA reading (if analyzed)</dt><dd>{evidence.analysis?.interpretation?.reading ?? 'unknown'} {evidence.analysis?.interpretation?.unit}</dd></div>
      {receipt && <><div><dt>Model</dt><dd>{receipt.returned_model ?? 'unknown'} · validation {receipt.validation_result}</dd></div><div><dt>Attempt</dt><dd>{receipt.attempt_id}</dd></div><div><dt>Latency</dt><dd>{receipt.latency_ms === null ? 'unknown' : `${receipt.latency_ms} ms measured`}</dd></div><div><dt>Revision</dt><dd>{receipt.source_revision ?? 'unknown / dirty checkout'}</dd></div></>}
      {evidence.analysis?.error && <div><dt>Diagnostic</dt><dd>{evidence.analysis.error}</dd></div>}
    </dl>{receipt && <HTTPDiagnostics receipt={receipt} />}<p className="notice">Validated output is a model interpretation, not equipment identity, diagnosis, authorization, or verified recovery. Upload metadata was stripped; stored images are served only through the existing local evidence endpoint, not committed or publicly hosted. Ordinary pressure must never be treated as differential pressure without a supporting instrument and unit.</p>
  </>;
}
