import type { PhotoAssessment, ServerEvidence, ServerState } from './api';
import type { Mutate } from './workspace';

const labels: Record<string, string> = {
  human_model_report_disagreement: 'The independent human report disputes or does not corroborate this photo; inspect both sources.',
  identity_unconfirmed: 'Photographed asset identity remains unconfirmed.',
  model_tag_disagrees_with_assignment: 'Model-read tag differs from the assigned asset; identity is unresolved.',
  human_reports_wrong_equipment: 'Operator reported different equipment.',
  reading_not_established: 'No readable numeric claim is established.',
  pressure_is_not_differential_pressure: 'Pressure does not satisfy the differential-pressure request.',
  measurement_type_unresolved: 'Measurement type does not establish the requested measurement.',
  handle_orientation_does_not_verify_position: 'Handle orientation does not verify internal valve position.',
  model_reports_uncertainty: 'The model reported uncertainty; inspect its reasons.',
  validated_interpretation_unavailable: 'No validated photographic interpretation is available.',
  human_model_readability_disagreement: 'Human and model disagree about readability; both records are retained.',
  human_model_numeric_disagreement: 'Human and model readings disagree; neither replaces the other.',
  stale_or_superseded: 'Photo is older than 30 minutes, superseded, or stale; obtain fresh evidence.',
};

export function PhotoPlanningAssessment({ value, expanded = false }: { value: PhotoAssessment; expanded?: boolean }) {
  return <div className="photo-planning-assessment">
    <p><strong>{value.status === 'usable' ? 'Usable planning claim' : `Planning: ${value.status}`}</strong> · model claim, not a verified measurement</p>
    {value.flags.includes('pressure_is_not_differential_pressure') && <p>Pressure is not differential pressure.</p>}
    <details open={expanded || undefined}><summary>Why this photo needs follow-up</summary>
      <ul>{value.flags.map(flag => <li key={flag}>{labels[flag] ?? 'Further review is required.'}</li>)}</ul>
      <p>No photo claim satisfies the correction checklist. Assignment and label transcription do not establish identity.</p>
      {value.claim && <p>Original model claim: {value.claim.measurement_type} · {value.claim.reading ?? 'no reading'} {value.claim.visible_unit ?? ''}. Uncertainty: {value.claim.reasons.join(', ') || 'none reported; factual accuracy unverified'}.</p>}
      <p className="caption">Source: {value.source} · task {value.task_id} · analysis {value.analysis_status ?? 'not analyzed'}. Freshness is wall-clock upload age (30-minute planning window), not a measurement timestamp.</p>
      {!!value.conflicting_refs.length && <p className="caption">Disputed with: {value.conflicting_refs.join(', ')}</p>}
    </details>
  </div>;
}

export function PhotoFollowUp({ state, disabled, mutate, inspect }: {
  state: ServerState; disabled: boolean; mutate: Mutate; inspect: (item: ServerEvidence) => void;
}) {
  const task = state.task;
  if (!task || !state.photo_planning) return null;
  const sources = state.evidence.filter(e => task.source_photo_ids?.includes(e.id));
  const latest = state.evidence.filter(e => e.task_id === task.id && e.photo_assessment).at(-1);
  const assessment = latest?.photo_assessment;
  const canForward = task.status === 'awaiting' && assessment?.analysis_status === 'interpreted'
    && assessment.claim && assessment.status !== 'stale';
  return <>
    {!!sources.length && <section className="section-surface photo-follow-up"><h2>Clarify photographic evidence</h2>
      <p>This observation references evidence associated with these photographs. Follow the registered task instructions; confirm equipment and measurement type independently.</p>
      {sources.map(e => <button className="button secondary" key={e.id} onClick={() => inspect(e)}>Inspect source photograph · assigned {e.asset_id}</button>)}
    </section>}
    {canForward && latest && <section className="section-surface photo-follow-up"><h2>Photo ready for follow-up review</h2>
      <p>Send this claim to Commander for the next observation decision. This does not accept its reading or complete the measurement task.</p>
      <button className="button secondary" disabled={disabled} onClick={() => void mutate(`/api/tasks/${task.id}/photo-follow-up`,
        { revision: task.revision, evidence_id: latest.id }, `photo-follow-up-${latest.id}-${task.revision}`)}>Send photo for follow-up planning</button>
    </section>}
  </>;
}
