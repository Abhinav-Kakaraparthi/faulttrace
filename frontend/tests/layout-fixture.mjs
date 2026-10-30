// Browser-only provider-free double. Never sent to a backend or used as live evidence.
export const run = '11111111-1111-4111-8111-111111111111';
export function layoutState(assigned = false) {
  const sample = { id: 'layout-sample', tick: 0, timestamp: '2026-10-30T10:00:00Z', flow: 85, pressure: 182, valve: 72, alarm: 'return_flow_low' };
  const task = { id: 'layout-task', revision: 1, asset_id: 'F-17', capability: 'READ_LOCAL_DP', status: 'awaiting',
    instruction: 'Offline browser test: observe the assigned indicator only. Do not operate equipment.',
    creation_source: 'offline browser test setup; not NVIDIA', explanation: 'Layout test assignment; no inference.' };
  return { incident: { id: run, revision: 1 }, test_output: true, inference_enabled: false, task: assigned ? task : null,
    tasks: assigned ? [task] : [], planning: [], planning_remaining: 4, events: [],
    photo_collection: { version: 1, assets: ['F-17', 'V-08'] },
    evidence: assigned ? [{ id: 'layout-photo', task_id: task.id, asset_id: 'F-17', kind: 'image', origin: 'synthetic-regression-fixture',
      fixture_id: null, status: 'collected', submitted_revision: 1, analysis: null, report: null, image_url: null,
      sha256: null, width: 960, height: 540, created_at: sample.timestamp }] : [],
    journey: { evidence_mode: 'task-evidence', test_output: true, clock: sample.timestamp, tick: 0, samples: [sample], observations: [],
      assessment: { eligible: false, working_diagnosis: null, source: 'deterministic fixture assessment',
        blockers: ['F-17_missing', 'V-08_missing'], evidence_refs: [sample.id], alternatives: ['Sensor discrepancy', 'Valve mismatch'] },
      policy: { freshness_seconds: 120, pressure_agreement_kpa: 8, restriction_pressure_kpa: [170, 195], restricted_flow_m3h: [80, 95],
        recovery_pressure_kpa: [25, 40], recovery_flow_m3h: [115, 125], valve_feedback_percent: [65, 80], window_seconds: 40, minimum_samples: 5 },
      action_id: 'SIMULATE_F17_FILTER_REPLACEMENT', approval_id: null, approval_current: false, approved_evidence_refs: [],
      maintenance_status: 'not_completed', recovery: { status: 'not_started', sample_count: 0, window_seconds: 0, sample_refs: [] } } };
}
