import type { ServerEvidence } from './api';
import { EvidencePhoto } from './EvidencePhoto';
import { evidenceStatus, evidenceTimestamp } from './evidencePresentation';
import { HTTPDiagnostics } from './HTTPDiagnostics';
import { PhotoInterpretation } from './PhotoInterpretation';

export function ServerEvidenceDetails({ evidence }: { evidence: ServerEvidence }) {
  const receipt = evidence.analysis?.receipt;
  return <section className="evidence-inspection">
    <div className="inspection-summary"><span className="pill amber">{evidenceStatus(evidence)}</span><strong>Assigned asset: {evidence.asset_id}</strong><time dateTime={evidence.created_at}>{evidenceTimestamp(evidence.created_at)} · wall-clock record</time></div>
    {evidence.kind === 'image' ? <EvidencePhoto evidence={evidence} /> : <p>Human report only: {evidence.report}. No image or image-based identity verification supplied.</p>}
    {evidence.status === 'collected' && !evidence.analysis && <p>Collection-only photograph / not analyzed. No pressure reading inferred.</p>}
    {evidence.analysis?.interpretation && <PhotoInterpretation value={evidence.analysis.interpretation} status={evidence.analysis.status} />}
    <details className="inspection-provenance"><summary>Provenance, evidence limits &amp; receipt</summary>
      <p className="notice">Assignment is not image-verified identity. Record visible tags as seen; do not rename a different asset. An ordinary pressure gauge does not establish differential pressure; a valve handle does not prove internal valve condition. Evidence cannot authorize correction or recovery.</p>
      <p>{evidence.origin === 'synthetic-fixture' ? 'Committed synthetic fixture / regression evidence, not an equipment photograph.' : evidence.kind === 'image' ? 'User-supplied image / source and authenticity not independently verified.' : 'Human-reported observation; not image-verified.'}</p>
      <dl className="evidence-facts">
        <div><dt>Origin</dt><dd>{evidence.origin} {evidence.fixture_id}</dd></div>
        <div><dt>Evidence ID</dt><dd>{evidence.id}</dd></div>
        <div><dt>Task</dt><dd>{evidence.asset_id} · application-assigned, not image-verified</dd></div>
        <div><dt>Submitted task revision</dt><dd>{evidence.submitted_revision}</dd></div>
        <div><dt>Human report</dt><dd>{evidence.kind === 'report' ? evidence.report : 'No human report in this image record'}</dd></div>
        <div><dt>Image-supported asset identity</dt><dd>Not assessed by assignment</dd></div>
        <div><dt>NVIDIA readability (if analyzed)</dt><dd>{evidence.analysis?.interpretation?.readability ?? 'Not analyzed'}</dd></div>
        {receipt && <><div><dt>Model</dt><dd>{receipt.returned_model ?? 'unknown'} · validation {receipt.validation_result}</dd></div><div><dt>Attempt</dt><dd>{receipt.attempt_id}</dd></div><div><dt>Latency</dt><dd>{receipt.latency_ms == null ? 'unknown' : `${receipt.latency_ms} ms measured`}</dd></div><div><dt>Revision</dt><dd>{receipt.source_revision ?? 'unknown / dirty checkout'}</dd></div>
          <div><dt>Known tokens</dt><dd>input {receipt.token_usage?.prompt_tokens ?? 'unknown'} / output {receipt.token_usage?.completion_tokens ?? 'unknown'} / total {receipt.token_usage?.total_tokens ?? 'unknown'} · Usage {receipt.usage_status} · Ledger {evidence.analysis?.accounting}</dd></div></>}
        {evidence.analysis?.error && <div><dt>Diagnostic</dt><dd>{evidence.analysis.error}</dd></div>}
      </dl>{receipt && <HTTPDiagnostics receipt={receipt} />}
      <p>Upload metadata was stripped. Full images remain private local evidence; they are not committed or publicly hosted. A validated interpretation is not proof of measurement validity, equipment identity or completed work.</p>
    </details>
  </section>;
}
