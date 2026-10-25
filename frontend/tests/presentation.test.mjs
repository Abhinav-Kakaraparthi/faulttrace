// Static React markup tests are not browser, CSS-layout or keyboard verification.
import { test, after } from 'node:test';
import assert from 'node:assert/strict';
import { build } from 'vite';
import { mkdtempSync, writeFileSync, rmSync } from 'node:fs';
import { resolve, join, sep } from 'node:path';
import { pathToFileURL } from 'node:url';

const root = process.cwd();
const temporary = mkdtempSync(resolve('node_modules/.ft008a-'));
after(() => {
  if (!temporary.startsWith(join(root, 'node_modules') + sep)) throw new Error('unsafe_cleanup_path');
  rmSync(temporary, { recursive: true, force: true });
});
const output = await build({ configFile: false, logLevel: 'silent',
  build: { ssr: 'tests/presentation-entry.tsx', write: false, rollupOptions: { output: { format: 'es' } } } });
const entry = output.output.find(item => item.type === 'chunk' && item.isEntry);
const file = join(temporary, 'render.mjs');
writeFileSync(file, entry.code);
const { renderJourney, renderEvidence, renderPlanningHistory, renderAudit, renderCommander, renderOperator } = await import(pathToFileURL(file));

function snapshot() {
  const observations = [
    { id: 'observation-pressure', asset_id: 'F-17', status: 'readable', reading: 180, unit: 'kPa', origin: 'simulated-human-report', timestamp: '2026-10-25T10:00:00Z' },
    { id: 'observation-valve', asset_id: 'V-08', status: 'intermediate', reading: null, unit: null, origin: 'simulated-human-report', timestamp: '2026-10-25T10:00:00Z' },
  ];
  const samples = Array.from({ length: 6 }, (_, i) => ({ id: `sample-${i}`, tick: i,
    timestamp: `2026-10-25T10:00:${String(i * 10).padStart(2, '0')}Z`,
    flow: i === 0 ? 85 : 120, pressure: i === 0 ? 182 : 32, valve: 72, alarm: i === 0 ? 'return_flow_low' : null }));
  return { incident: { id: 'incident-test', revision: 9 }, task: null, evidence: [], planning: [],
    planning_remaining: 4, inference_enabled: false,
    events: [ { sequence: 1, kind: 'simulated_correction_approved', created_at: '2026-10-25T12:01:00Z' },
      { sequence: 2, kind: 'simulated_filter_replacement_completed', created_at: '2026-10-25T12:02:00Z' } ],
    journey: { clock: samples.at(-1).timestamp, tick: 5, samples, observations,
      assessment: { eligible: false, working_diagnosis: null, source: 'deterministic fixture assessment',
        blockers: ['pressure_not_corroborated'], evidence_refs: ['sample-5'], alternatives: ['Sensor discrepancy', 'Valve mismatch'] },
      policy: { freshness_seconds: 120, pressure_agreement_kpa: 8, restriction_pressure_kpa: [170,195],
        restricted_flow_m3h: [80,95], recovery_pressure_kpa: [25,40], recovery_flow_m3h: [115,125],
        valve_feedback_percent: [65,80], window_seconds: 40, minimum_samples: 5 },
      action_id: 'SIMULATE_F17_FILTER_REPLACEMENT', approval_id: 'approval-test', approval_current: false,
      approved_evidence_refs: ['sample-0', 'observation-pressure', 'observation-valve'],
      maintenance_status: 'simulated_replacement_completed',
      recovery: { status: 'verified', sample_count: 5, window_seconds: 40, sample_refs: samples.slice(1).map(s => s.id) } },
  };
}

test('completed journey has a coherent scoped record and no correction controls in either view', () => {
  const state = snapshot();
  for (const view of ['commander', 'operator']) {
    const html = renderJourney(state, view);
    assert.match(html, /Simulated operating recovery verified/);
    assert.match(html, /Journey evidence record/);
    assert.match(html, /180 kPa/);
    assert.match(html, /V-08 \/ intermediate/);
    assert.match(html, /5 post-action samples spanning 40 simulated seconds/);
    assert.match(html, /Simulated replacement completed/);
    assert.doesNotMatch(html, /Approve simulated correction|Complete simulated filter replacement|Record local pressure report/);
    assert.match(html, /Continue simulation \(optional\)/);
    assert.ok(html.indexOf('journey-outcome') < html.indexOf('journey-record'));
    const evidence = renderEvidence(state);
    assert.match(evidence, /Image and planner-task evidence/);
    assert.match(evidence, /No image or planner-task submissions/);
    assert.match(evidence, /2 simulated journey observations/);
    assert.doesNotMatch(evidence, /No evidence submitted\./);
  }
});

test('stored references, every telemetry value and zero values render without empty bullets or cells', () => {
  const state = snapshot();
  state.journey.samples[1].flow = 0;
  const html = renderJourney(state, 'commander');
  for (const ref of state.journey.approved_evidence_refs) assert.ok(html.includes(`<code>${ref}</code>`));
  const table = html.match(/<tbody>([\s\S]*?)<\/tbody>/)[1];
  assert.equal((table.match(/<tr>/g) || []).length, 6);
  for (const sample of state.journey.samples) {
    assert.ok(table.includes(sample.id));
    for (const value of [sample.flow, sample.pressure, sample.valve]) assert.ok(table.includes(`<td>${value}</td>`));
    assert.ok(table.includes(sample.timestamp));
  }
  assert.match(table, /<td>0<\/td>/);
  assert.doesNotMatch(html, /<li[^>]*>\s*<\/li>|<td[^>]*>\s*<\/td>/);
  assert.match(html, /tabindex="0" role="region" aria-label="Scrollable simulated telemetry table"/);
});

test('missing snapshot values are explicit unknowns with no invented reference links', () => {
  const state = snapshot();
  state.journey.approved_evidence_refs = ['', 'not-in-snapshot'];
  state.journey.samples[0].flow = null;
  state.journey.samples[0].alarm = undefined;
  const html = renderJourney(state, 'commander');
  assert.match(html, /Reference unavailable/);
  assert.match(html, /Reference not present in this snapshot/);
  assert.match(html, /<td>Unknown<\/td>/);
  assert.doesNotMatch(html, /href=/);
});

test('simulated measurement timestamps and wall-clock audit timestamps have separate labels', () => {
  const state = snapshot();
  const html = renderJourney(state, 'operator');
  assert.match(html, /Simulated measurement time \(UTC\)/);
  assert.match(html, /not wall-clock audit times/);
  assert.match(html, /Approval recorded: <time datetime="2026-10-25T12:01:00Z"/i);
  assert.match(html, /Simulated completion recorded: <time datetime="2026-10-25T12:02:00Z"/i);
  const history = renderAudit(state);
  assert.match(history, /Wall-clock audit history \(2\)/);
  assert.match(history, /Wall-clock UTC: 2026-10-25T12:02:00Z/);
  assert.doesNotMatch(history, /2026-10-25T10:00/);
});

test('planning history retains attempts but provides no new request or task action', () => {
  const state = snapshot();
  state.planning = [{ id: 'attempt-test', status: 'escalated', context_revision: 3, proposal: null }];
  const html = renderPlanningHistory(state);
  assert.match(html, /Human investigation requested/);
  assert.match(html, /attempt-test/);
  assert.doesNotMatch(html, /<button|Choose next observation|Open operator task/);
});

test('operator evidence entry and commander approval stay available before correction; failed verification never says verified', () => {
  const state = snapshot();
  state.journey.recovery.status = 'not_started';
  state.journey.maintenance_status = 'not_completed';
  state.journey.assessment.eligible = true;
  assert.match(renderJourney(state, 'commander'), /Approve simulated correction/);
  const operator = renderJourney(state, 'operator');
  assert.match(operator, /Record local pressure report/);
  assert.ok(operator.indexOf('Submit simulated field observations') < operator.indexOf('HUMAN-APPROVED SIMULATION'));
  state.journey.recovery.status = 'failed';
  state.journey.maintenance_status = 'simulated_replacement_completed';
  const failed = renderJourney(state, 'commander');
  assert.match(failed, /Recovery verification failed/);
  assert.doesNotMatch(failed, /Simulated operating recovery verified/);
});


test('dedicated Commander and Operator render the same stored completed incident with different responsibilities', () => {
  const state = snapshot();
  const before = JSON.stringify(state);
  const commander = renderCommander(state);
  const operator = renderOperator(state);
  for (const html of [commander, operator]) {
    assert.match(html, /incident-test/);
    assert.match(html, /evidence revision 9/);
    assert.match(html, /180 kPa/);
    assert.match(html, /V-08 \/ intermediate/);
    assert.match(html, /Simulated operating recovery verified/);
    for (const ref of state.journey.approved_evidence_refs) assert.ok(html.includes(ref));
  }
  assert.match(commander, /Process overview/);
  assert.match(commander, /Stored simulated telemetry/);
  assert.match(commander, /32 kPa \/ simulated/);
  assert.doesNotMatch(commander, /184 kPa \/ ELEVATED|62 kPa \/ BASELINE/);
  assert.match(commander, /NVIDIA observation planning/);
  assert.doesNotMatch(operator, /Choose next observation|Approve simulated correction|Decline \/ revoke|Start .*incident|Advance 10 simulated seconds|Process overview|NVIDIA observation planning/);
  assert.match(operator, /No further operator action is required/);
  assert.equal(JSON.stringify(state), before);
});

test('approval and incident creation belong to Commander; approved completion belongs to Operator', () => {
  const state = snapshot();
  state.journey.maintenance_status = 'not_completed';
  state.journey.recovery.status = 'not_started';
  state.journey.assessment.eligible = true;
  assert.match(renderCommander(state), /Approve simulated correction/);
  assert.doesNotMatch(renderOperator(state), /Approve simulated correction|Decline \/ revoke|Choose next observation/);
  assert.match(renderOperator(state), /Record local pressure report/);
  state.journey.approval_current = true;
  assert.match(renderOperator(state), /Complete simulated filter replacement/);
  assert.doesNotMatch(renderCommander(state), /Complete simulated filter replacement/);
  state.journey.maintenance_status = 'simulated_replacement_completed';
  state.journey.recovery.status = 'observing';
  assert.match(renderOperator(state), /Completion acknowledged/);
  assert.doesNotMatch(renderOperator(state), /Advance 10 simulated seconds/);
  const empty = { ...state, incident: null, task: null, journey: null, evidence: [] };
  assert.match(renderCommander(empty), /Start restriction-to-recovery simulation/);
  assert.match(renderCommander(empty), /Start observation-only incident/);
  assert.match(renderOperator(empty), /Waiting for an assignment/);
  assert.doesNotMatch(renderOperator(empty), /Start .*incident|Choose next observation|Approve simulated correction/);
});

function imageTaskState() {
  const state = snapshot();
  state.journey = null;
  state.task = { id: 'assigned-task', revision: 2, asset_id: 'F-17', capability: 'READ_LOCAL_DP',
    status: 'awaiting', instruction: 'Read the assigned local indicator only. Do not operate equipment.',
    creation_source: 'validated NVIDIA proposal', explanation: 'An independent observation is needed.' };
  state.evidence = [{ id: 'image-evidence', task_id: 'assigned-task', kind: 'image', origin: 'user-upload',
    fixture_id: null, status: 'pending', submitted_revision: 1, analysis: null, created_at: '2026-10-25T12:00:00Z' }];
  state.inference_enabled = true;
  return state;
}

test('assigned image/report/refusal and opt-in analysis controls are in Operator; Commander only reviews', () => {
  const state = imageTaskState();
  const operator = renderOperator(state);
  assert.match(operator, /Read the assigned local indicator only/);
  assert.match(operator, /Submit image/);
  assert.match(operator, /Analyze image/);
  assert.match(operator, /Report cannot access/);
  assert.match(operator, /Report wrong equipment/);
  assert.match(operator, /Report unreadable/);
  assert.doesNotMatch(operator, /Choose next observation|Start .*incident|Approve simulated correction/);
  const commander = renderCommander(state);
  assert.match(commander, /Choose next observation/);
  assert.doesNotMatch(commander, /Submit image|>Analyze image</);
  assert.match(commander, /No timestamped simulator measurements/);
  assert.match(commander, /Pressure unavailable/);
  assert.doesNotMatch(commander, /184 kPa|62 kPa|>86 /);
  state.inference_enabled = false;
  assert.match(renderOperator(state), /<button[^>]*disabled[^>]*>Analyze image</);
  state.task.asset_id = 'V-08';
  state.task.capability = 'OBSERVE_POSITION';
  assert.match(renderOperator(state), /Report intermediate/);
  assert.match(renderOperator(state), /Report cannot determine/);
});

test('combined evidence retains scopes without pretending model evidence participates in recovery policy', () => {
  const state = imageTaskState();
  state.journey = snapshot().journey;
  for (const html of [renderCommander(state), renderOperator(state)]) {
    assert.match(html, /Investigation evidence/);
    assert.match(html, /Journey evidence record/);
    assert.match(html, /user-upload/);
    assert.match(html, /NVIDIA task evidence/);
    assert.match(html, /not consumed by the simulated correction\/recovery assessment/);
    assert.doesNotMatch(html, /No evidence submitted\./);
  }
});

test('both dedicated pages have meaningful loading/offline states; stale snapshots disable mutation controls', () => {
  for (const render of [renderCommander, renderOperator]) {
    assert.match(render(null, { connection: 'loading', disabled: true }), /Loading server state/);
    assert.match(render(null, { connection: 'paused', disabled: true }), /Backend is not available/);
    assert.doesNotMatch(render(null, { connection: 'paused', disabled: true }), /180 kPa|recovery verified/);
  }
  const state = imageTaskState();
  const operator = renderOperator(state, { connection: 'paused', disabled: true });
  assert.match(operator, /<fieldset[^>]*disabled/);
  assert.match(operator, /<button[^>]*disabled[^>]*>Analyze image</);
  const commander = renderCommander(state, { connection: 'paused', disabled: true });
  assert.match(commander, /<button[^>]*disabled[^>]*>Choose next observation</);
});
