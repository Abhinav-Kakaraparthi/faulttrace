import { useEffect, useState } from 'react';
import { type ServerEvidence as Evidence, type ServerState } from './api';
import { HTTPDiagnostics } from './HTTPDiagnostics';

export const statusLabel: Record<string, string> = {
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
      </span><h3>{item.kind === 'image' ? 'Image observation' : `Human report: ${item.report}`}</h3>
      <p>Source: {item.origin}{item.fixture_id ? ` / ${item.fixture_id}` : ''} · Task revision {item.submitted_revision}</p>
      {item.analysis?.interpretation && <p className="model-reading">Model interpretation: {item.analysis.interpretation.readability === 'readable' ? `${item.analysis.interpretation.reading} ${item.analysis.interpretation.unit}` : 'unreadable — reading and unit unknown'}</p>}
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
  const [imageFailed, setImageFailed] = useState(false);
  useEffect(() => setImageFailed(false), [evidence.id]);
  const receipt = evidence.analysis?.receipt;
  return <><span className="pill amber">{evidenceStatus(evidence)}</span>
    {evidence.image_url ? imageFailed ? <p className="notice">Stored image unavailable. Metadata may remain, but image availability is not established.</p> : <img className="evidence-image" src={evidence.image_url} onError={() => setImageFailed(true)} alt="Privately stored submitted evidence; asset identity is not verified by this image" /> : <p>No image supplied. Human report only: {evidence.report}. Position reports are not image-verified.</p>}
    <dl className="evidence-facts">
      <div><dt>Origin</dt><dd>{evidence.origin} {evidence.fixture_id}</dd></div>
      <div><dt>Evidence ID</dt><dd>{evidence.id}</dd></div>
      <div><dt>Task</dt><dd>{evidence.asset_id} · application-assigned, not image-verified</dd></div>
      <div><dt>Readability</dt><dd>{evidence.analysis?.interpretation?.readability ?? (evidence.report === 'unreadable' ? 'human-reported unreadable' : 'not established')}</dd></div>
      <div><dt>Reading</dt><dd>{evidence.analysis?.interpretation?.reading ?? 'unknown'} {evidence.analysis?.interpretation?.unit}</dd></div>
      {receipt && <><div><dt>Model</dt><dd>{receipt.returned_model ?? 'unknown'} · validation {receipt.validation_result}</dd></div><div><dt>Attempt</dt><dd>{receipt.attempt_id}</dd></div><div><dt>Latency</dt><dd>{receipt.latency_ms === null ? 'unknown' : `${receipt.latency_ms} ms measured`}</dd></div><div><dt>Revision</dt><dd>{receipt.source_revision ?? 'unknown / dirty checkout'}</dd></div></>}
      {evidence.analysis?.error && <div><dt>Diagnostic</dt><dd>{evidence.analysis.error}</dd></div>}
    </dl>{receipt && <HTTPDiagnostics receipt={receipt} />}<p className="notice">Validated output is a model interpretation, not equipment identity, diagnosis, authorization, or verified recovery. Upload metadata was stripped; private image bytes stay outside the frontend.</p>
  </>;
}
