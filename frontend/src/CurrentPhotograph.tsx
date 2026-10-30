import type { ServerState, ServerEvidence } from './api';
import type { Mutate } from './workspace';
import { PhotoInterpretation } from './PhotoInterpretation';
import { reviewablePhotos } from './photoSubmission';

export function CurrentPhotograph({ state, disabled, mutate, inspect }: {
  state: ServerState; disabled: boolean; mutate: Mutate; inspect?: (item: ServerEvidence) => void;
}) {
  const task = state.task;
  const photo = state.evidence.filter(item => item.task_id === task?.id && item.kind === 'image').at(-1);
  if (!task || !photo) return null;
  const analysis = photo.analysis;
  const current = reviewablePhotos(state).some(item => item.id === photo.id);
  const ready = photo.status === 'collected' && !analysis;
  return <section className="current-photograph" aria-label="Current photograph" aria-live="polite">
    <h3>Current photograph</h3>
    <p>{!analysis ? 'Photograph stored; analysis has not been requested.' : analysis.status === 'pending' ? 'NVIDIA is analyzing this photograph. The result will appear here.' : `Image analysis: ${analysis.status.replaceAll('_', ' ')}.`}</p>
    {inspect && <button className="button secondary" type="button" onClick={() => inspect(photo)}>Inspect current photograph</button>}
    {ready && <button className="button primary" type="button" disabled={disabled || !state.inference_enabled || state.photo_analysis?.contract !== 'photo-observation-v1'}
      onClick={() => void mutate(`/api/evidence/${photo.id}/analyze-photo`, { revision: task.revision }, `photo-analysis-${photo.id}-${task.revision}`)}>Analyze photograph with NVIDIA</button>}
    {analysis?.interpretation && <PhotoInterpretation value={analysis.interpretation} status={analysis.status} />}
    {current && <><p><strong>Next: independently review the photograph below.</strong> Enter only the identity and measurement you can establish. If the tag, instrument type or reading is unclear, keep it unresolved and request clarification.</p>
      <a className="button secondary" href="#independent-observation">Review photographic claim</a></>}
    {analysis?.interpretation && !current && <p className="notice">{analysis.contract !== 'photo-observation-v1'
      ? 'This result uses the legacy test-display contract and cannot be confirmed as photographic evidence. It remains in history; collect a real photograph for a new observation or escalate the unresolved task.'
      : 'This is not an accepted current interpretation. Review its analysis status; do not confirm a stale, failed or interrupted result.'}</p>}
    {analysis?.status === 'uncertain' && <p className="notice">Analysis was interrupted. No request will be retried automatically. Review its recorded status before any further action.</p>}
  </section>;
}
