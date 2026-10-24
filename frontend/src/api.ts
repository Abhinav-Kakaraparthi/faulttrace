export type Receipt = {
  attempt_id: string; requested_model: string; returned_model: string | null;
  validation_result: string; timestamp: string; latency_ms: number | null;
  source_revision: string | null; usage_status: string;
  token_usage: { prompt_tokens: number | null; completion_tokens: number | null; total_tokens: number | null } | null;
};
export type Interpretation = { readability: 'readable' | 'unreadable'; reading: number | null; unit: string | null; evidence_ref: string };
export type ServerEvidence = {
  id: string; task_id: string; kind: 'image' | 'report'; origin: string; fixture_id: string | null;
  sha256: string | null; width: number | null; height: number | null; status: string; report: string | null;
  created_at: string; image_url: string | null; submitted_revision: number;
  analysis: { id: string; status: string; interpretation: Interpretation | null; receipt: Receipt | null; error: string | null; accounting: string } | null;
};
export type ServerState = {
  incident: { id: string; created_at: string } | null;
  task: { id: string; revision: number; status: string; asset_id: string; creation_source: string } | null;
  evidence: ServerEvidence[];
  events: { sequence: number; kind: string; evidence_id: string | null; created_at: string }[];
  inference_enabled: boolean;
};
const errors: Record<string, string> = {
  stale_task: 'Task changed in another tab. Refresh the task before submitting again.',
  stale_or_unanalyzable_evidence: 'This evidence is stale or cannot be analyzed. Load the current task.',
  inference_disabled: 'Inference is disabled on this server. See the local startup guide.',
  missing_credentials: 'The backend process has no provider credential. No request was made.',
  image_size_invalid: 'Choose a PNG/JPEG image no larger than 2 MiB.',
  request_too_large: 'The submission exceeds the allowed size.',
  image_type_invalid: 'Only PNG and JPEG images are supported.',
  image_bytes_or_dimensions_invalid: 'Image could not be decoded or exceeds dimension/pixel limits.',
  fixture_provenance_mismatch: 'The submitted bytes do not match the selected committed fixture.',
  idempotency_conflict: 'A request identifier was reused with different content. Reload the current task.',
  task_not_accepting_evidence: 'This task already has a submission. Request another observation first.',
  analysis_in_progress: 'Analysis is already pending. It will not be automatically repeated.',
};
export async function apiResponse(response: Response) {
  if (!response.ok) {
    const value = await response.json().catch(() => ({}));
    throw new Error(errors[value.error] ?? 'Request failed. Refresh the current task; no automatic write retry occurred.');
  }
  return response.json();
}
