export type Sample = { id: string; tick: number; timestamp: string; flow: number; pressure: number; valve: number; alarm: string | null };
export type SimObservation = { evidence_id?: string; task_id?: string; human_observation?: import('./api').HumanObservationRecord; id: string; asset_id: string; status: string; reading: number | null; unit: string | null; origin: string; timestamp: string };
export type JourneyState = {
  evidence_mode?: 'task-evidence' | 'legacy-simulation'; test_output?: boolean;
  label: string; clock: string; tick: number; samples: Sample[]; observations: SimObservation[];
  time_mode?: 'paused-demo' | 'wall-clock-evidence';
  monitoring?: { status: 'running' | 'completed' | 'interrupted'; target_tick: number } | null;
  assessment: { source: string; working_diagnosis: string | null; evidence_refs: string[]; blockers: string[]; eligible: boolean; alternatives: string[] };
  policy: { freshness_seconds: number; pressure_agreement_kpa: number; restriction_pressure_kpa: number[]; restricted_flow_m3h: number[]; recovery_pressure_kpa: number[]; recovery_flow_m3h: number[]; valve_feedback_percent: number[]; window_seconds: number; minimum_samples: number };
  action_id: string; approval_id?: string | null; approval_current: boolean; approved_evidence_refs: string[];
  maintenance_status: string;
  recovery: { status: 'not_started' | 'observing' | 'verified' | 'failed'; sample_count: number; window_seconds: number; sample_refs: string[] };
};

export function approvalBlocker(journey: JourneyState): string | null {
  if (journey.maintenance_status !== 'not_completed') return 'The simulated replacement has already been completed.';
  if (!journey.assessment.eligible) return 'Resolve the required evidence gaps before approving a correction.';
  if (journey.approval_current) return 'Approval is recorded. Operator can complete the simulated correction.';
  return null;
}

export function recoveryLabel(status: JourneyState['recovery']['status']): string {
  return { not_started: 'Recovery not assessed', observing: 'Observing post-correction samples',
    verified: 'Simulated operating recovery verified', failed: 'Recovery verification failed' }[status];
}

export function canApprove(journey: JourneyState, revision: number, consentRevision: number | null): boolean {
  return approvalBlocker(journey) === null && consentRevision === revision;
}

export function canExecute(journey: JourneyState): boolean {
  return journey.maintenance_status === 'not_completed' && !!journey.approval_id && journey.approval_current && journey.assessment.eligible;
}
