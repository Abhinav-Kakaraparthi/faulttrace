import type { ServerState } from './api';
import type { UploadProgress } from './photoUpload';

export type PhotoSubmission = 'unconfirmed' | 'stored' | 'analysis_requested' | 'stored_analysis_stopped';
export type SubmitPhoto = (task: NonNullable<ServerState['task']>, blob: Blob, identity: string,
  analyze: boolean, progress: UploadProgress) => Promise<PhotoSubmission>;

// Confirmation requires the photographic contract, never the older test-display contract.
export function reviewablePhotos(state: ServerState) {
  return state.evidence.filter(item => item.task_id === state.task?.id && item.kind === 'image'
    && item.analysis?.contract === 'photo-observation-v1' && item.analysis.status === 'interpreted'
    && item.analysis.interpretation && 'category' in item.analysis.interpretation);
}
