import type { PhotoObservation } from './PhotoInterpretation';
import type { JourneyState } from './journeyState';
export type Receipt = {
  attempt_id: string; requested_model: string; returned_model: string | null;
  validation_result: string; timestamp: string; latency_ms: number | null;
  source_revision: string | null; usage_status: string;
  error?: string; http_status?: number | null; http_error_category?: string | null;
  token_usage: { prompt_tokens: number | null; completion_tokens: number | null; total_tokens: number | null } | null;
};
export type FixtureInterpretation = { readability: 'readable' | 'unreadable'; reading: number | null; unit: string | null; evidence_ref: string };
export function httpDiagnosticSummary(receipt: Pick<Receipt, 'error' | 'http_status' | 'http_error_category'>): string | null {
  if (receipt.error !== 'provider_http_error') return null;
  return `Provider HTTP status: ${receipt.http_status ?? 'unknown'} · Category: ${receipt.http_error_category ?? 'unknown'}. Status category only; provider cause is not established. Error body and headers are not retained.`;
}
export type Interpretation = FixtureInterpretation | PhotoObservation;
export type PhotoAssessment = {
  evidence_id: string; evidence_ref: string; task_id: string; assigned_asset: string;
  source: string; timestamp: string; analysis_status: string | null;
  status: 'usable' | 'disputed' | 'incompatible' | 'unresolved' | 'stale';
  identity_status: string; flags: string[]; conflicting_refs: string[];
  claim: Omit<PhotoObservation, 'label_text' | 'evidence_ref'> | null;
};
export type HumanObservationRecord = {
  photo_id: string | null; decision: string; observed_asset_id: string; measurement_type: string;
  reading: number | null; unit: string | null; position: string | null; normalized_kpa: number | null;
  flags: string[]; status: string; timestamp: string; received_at: string; source: string;
};
export type ServerEvidence = {
  id: string; task_id: string; asset_id: string; kind: 'image' | 'report'; origin: string; fixture_id: string | null;
  sha256: string | null; width: number | null; height: number | null; status: string; report: string | null;
  created_at: string; image_url: string | null; submitted_revision: number;
  human_observation?: HumanObservationRecord; test_output?: boolean;
  photo_assessment?: PhotoAssessment;
  analysis: { contract?: string; id: string; status: string; interpretation: Interpretation | null; receipt: Receipt | null; error: string | null; accounting: string } | null;
};
export type ServerState = {
  demo?: { template_actions: string[]; assignment_remaining: number };
  test_output?: boolean;
  photo_planning?: { version: number };
  photo_analysis?: { version: number; contract: string };
  photo_collection?: { version: number; assets: string[] };
  journey?: JourneyState | null;
  incident: { id: string; created_at: string; revision: number } | null;
  task: { source_photo_ids?: string[]; id: string; revision: number; status: string; asset_id: string; capability: string; creation_source: string; explanation: string; instruction: string } | null;
  planning_remaining: number;
  planning: { id: string; context_revision: number; status: string; error: string | null; explanation: string | null; accounting: string; task_id: string | null; receipt: Receipt | null; proposal: { kind: string; asset_id: string; capability: string; explanation_code: string; evidence_refs: string[] } | null }[];
  evidence: ServerEvidence[];
  events: { sequence: number; kind: string; evidence_id: string | null; created_at: string }[];
  inference_enabled: boolean;
};
const errors: Record<string, string> = {
  demo_session_required: 'Choose Try demo to open a session.',
  demo_session_expired: 'Demo session expired. Choose Try demo to begin again; previous investigations are retained.',
  demo_session_changed: 'Demo restarted in another tab. Resume its current investigation; no write was replayed.',
  demo_csrf_required: 'Demo request could not be verified. Refresh the session before another action.',
  demo_origin_required: 'This demo requires its configured same-origin application.',
  demo_capacity: 'This local demo has reached its session capacity. Ask the host to provide a fresh review instance.',
  demo_restart_limit: 'This session has reached its restart limit. Previous investigations remain retained.',
  demo_assignment_budget: 'This investigation has reached its demo assignment limit.',
  demo_action_unavailable: 'That observation is unavailable. Preserve the evidence and clarify or escalate.',
  demo_upload_limit: 'This demo investigation has reached its photograph limit.',
  authentication_required: 'Access ended. Enter your token again. Pending writes may have reached the server; none will be replayed.',
  access_denied: 'Access denied. Your role or incident grant does not permit this request. Refresh access after administrator changes.',
  storage_or_internal_failure: 'Server storage or internal failure. State may have changed; refresh before another action.',
  task_observation_required: 'Record evidence on the assigned Operator task; untasked reports cannot support this investigation.',
  task_investigation_required: 'This historical run uses the legacy journey. Start a fresh isolated investigation to use task-linked reports.',
  invalid_human_observation: 'Choose an observed identity/type and valid reading/unit or position. No model value is substituted.',
  independent_report_required: 'Confirm that you independently entered the observation; assignment and model output are not verification.',
  photo_follow_up_unavailable: 'This photograph cannot be sent for follow-up. Refresh and review its analysis and freshness.',
  photo_contract_not_applicable: 'This endpoint analyzes collected photographs only; existing fixture analysis remains separate.',
  stale_photo_result: 'Investigation changed during analysis. The stale result cannot be used; accounting is preserved.',
  photo_analysis_unsupported: 'This photograph is collection-only. Analog gauges and valve images are outside the validated vision contract.',
  invalid_evidence_purpose: 'This photo purpose is not supported. Refresh the assigned observation.',
  simulation_requires_fresh_run: 'Start FT-008 in a fresh isolated data directory. Existing incidents are preserved.',
  correction_evidence_blocked: 'Required evidence is missing, stale or disputed. Review the deterministic assessment.',
  stale_or_missing_approval: 'Approval is missing or stale. Commander must review the current evidence revision.',
  simulation_observations_closed: 'This correction has executed. Its pre-action evidence remains preserved.',
  simulation_already_executed: 'The simulated replacement has already executed. Refresh to inspect recovery.',
  simulation_step_budget_exhausted: 'This fixture run has reached its 360-step limit.',
  invalid_simulated_observation: 'Choose a registered report and a finite reading in the synthetic range.',
  stale_context: 'Investigation changed. Refresh; the old planner result cannot create a task.',
  active_task_conflict: 'Complete or report the current blocking task before choosing another observation.',
  planning_in_progress: 'A planning request is pending. No additional call was made.',
  planning_budget_exhausted: 'All four planning turns are reserved. Continue with human investigation.',
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
export class APIError extends Error {
  status: number;
  code: string;
  constructor(status: number, code: string) {
    super(errors[code] ?? 'Request failed. Refresh the current task; no automatic write retry occurred.');
    this.status = status; this.code = code;
  }
}
export async function apiResponse(response: Response) {
  if (!response.ok) {
    const value = await response.json().catch(() => ({}));
    throw new APIError(response.status, Object.hasOwn(errors, value.error) ? value.error : 'request_failed');
  }
  try { return await response.json(); }
  catch { throw new Error('Server response could not be read. State may have changed; refresh before another action.'); }
}
