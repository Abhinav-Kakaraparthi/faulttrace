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
const { renderJourney, renderEvidence, renderPlanningHistory, renderAudit } = await import(pathToFileURL(file));

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
