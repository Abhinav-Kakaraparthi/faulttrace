// Presentation of existing server blockers only; no eligibility decisions here.
const labels: Record<string, string> = {
  'F-17_missing': 'F-17: local differential-pressure report missing.',
  'V-08_missing': 'V-08: position report missing.',
  active_observation_or_planning: 'Complete the active observation before requesting another.',
  photographic_claim_requires_independent_review: 'Photograph needs an independent human review.',
  human_observation_wall_clock_stale: 'Human report is stale; fresh evidence is required.',
  telemetry_missing_or_stale: 'Telemetry is missing or stale.',
  pressure_reports_conflict: 'Local pressure reports disagree.',
  differential_pressure_required: 'A differential-pressure report is required; pressure alone is incompatible.',
  human_disputes_photo: 'Human and photographic observations remain disputed.',
};
export const evidenceGapLabel = (code: string) => labels[code] ?? code.replaceAll('_', ' ');
