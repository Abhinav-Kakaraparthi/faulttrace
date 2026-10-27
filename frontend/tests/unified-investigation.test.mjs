// Static component checks only; not desktop/mobile, keyboard or browser evidence.
import { test, after } from 'node:test';
import assert from 'node:assert/strict';
import { build } from 'vite';
import { mkdtempSync, writeFileSync, rmSync } from 'node:fs';
import { resolve, join, sep } from 'node:path';
import { pathToFileURL } from 'node:url';

const root = process.cwd();
const temporary = mkdtempSync(resolve('node_modules/.unified-'));
after(() => {
  if (!temporary.startsWith(join(root, 'node_modules') + sep)) throw new Error('unsafe_cleanup_path');
  rmSync(temporary, { recursive: true, force: true });
});
const output = await build({ configFile: false, logLevel: 'silent',
  build: { ssr: 'tests/presentation-entry.tsx', write: false, rollupOptions: { output: { format: 'es' } } } });
const entry = output.output.find(item => item.type === 'chunk' && item.isEntry);
const file = join(temporary, 'render.mjs'); writeFileSync(file, entry.code);
const { renderCommander, renderOperator, renderEvidenceDetails } = await import(pathToFileURL(file));

function state() {
  const human = { decision:'confirm', photo_id:'photo-a', observed_asset_id:'F-17', measurement_type:'differential_pressure',
    reading:180, unit:'kPa', position:null, normalized_kpa:180, flags:[], status:'readable',
    received_at:'2026-10-27T14:00:00Z', timestamp:'2026-10-27T13:00:00Z', source:'simulated-human-report' };
  const photo = { id:'photo-a', task_id:'task-a', asset_id:'F-17', kind:'image', origin:'user-upload', status:'collected',
    image_url:'/api/evidence/photo-a/image', created_at:'2026-10-27T14:00:00Z', submitted_revision:1,
    analysis:{id:'analysis-a', status:'interpreted', contract:'photo-observation-v1', receipt:null, accounting:'recorded',
      interpretation:{ category:'gauge', readability:'readable', measurement_type:'differential_pressure', reading:180,
        visible_unit:'kPa', label_text:null, valve_orientation:'not_applicable', reasons:[], evidence_ref:'evidence-photo-a' } } };
  const report = { id:'report-a', task_id:'task-a', asset_id:'F-17', kind:'report', origin:'human-report', status:'accepted',
    report:'readable', created_at:'2026-10-27T14:00:00Z', human_observation:human, analysis:null };
  const sample = {id:'sample-a', tick:0, timestamp:'2026-10-27T13:00:00Z', flow:85, pressure:182, valve:72, alarm:'return_flow_low'};
  return { incident:{id:'incident-a', revision:5}, task:{ id:'task-a', revision:4, asset_id:'F-17', capability:'READ_LOCAL_DP',
      status:'awaiting', creation_source:'validated NVIDIA proposal', explanation:'Independent observation required.', instruction:'Observe differential pressure only.' },
    evidence:[photo,report], planning:[], planning_remaining:3, events:[], inference_enabled:false,
    photo_collection:{version:1, assets:['F-17','V-08']}, photo_analysis:{version:1, contract:'photo-observation-v1'},
    journey:{ evidence_mode:'task-evidence', test_output:false, clock:sample.timestamp, tick:0, samples:[sample],
      observations:[{id:'evidence-report-a', asset_id:'F-17', status:'readable', reading:180, unit:'kPa', origin:'simulated-human-report', timestamp:sample.timestamp}],
      assessment:{eligible:false, source:'deterministic fixture evidence assessment; not model output', working_diagnosis:null,
        evidence_refs:['sample-a','evidence-report-a'], blockers:['V-08_missing'], alternatives:['Sensor discrepancy','Valve mismatch']},
      policy:{freshness_seconds:120, pressure_agreement_kpa:8, restriction_pressure_kpa:[170,195], restricted_flow_m3h:[80,95], recovery_pressure_kpa:[25,40], recovery_flow_m3h:[115,125], valve_feedback_percent:[65,80], window_seconds:40, minimum_samples:5},
      action_id:'SIMULATE_F17_FILTER_REPLACEMENT', approval_id:null, approval_current:false,
      approved_evidence_refs:[], maintenance_status:'not_completed', recovery:{status:'not_started', sample_count:0, window_seconds:0, sample_refs:[]} } };
}

test('Operator independent report starts blank, never confirms model values or assignment by default', () => {
  const html = renderOperator(state());
  assert.match(html, /Record your independent observation/);
  for (const label of ['Choose source','Choose observed identity','Choose measurement type']) {
    assert.ok(html.includes(`<option value="" selected="">${label}</option>`));
  }
  assert.doesNotMatch(html, /<input[^>]*value="180"|<option[^>]*selected[^>]*>F-17/);
  assert.match(html, /No model value is prefilled/);
  assert.match(html, /Dispute a photographic claim/);
  assert.doesNotMatch(html, /Record local pressure report|Submit simulated field observations|Choose next observation|Approve simulated correction/);
});

test('shared recovery references inspect canonical task evidence without parallel-workflow warning', () => {
  for (const render of [renderCommander, renderOperator]) {
    const html = render(state());
    assert.match(html, /same task evidence below/);
    assert.match(html, /Inspect shared task evidence/);
    assert.match(html, /Shared task evidence and independent reports/);
    assert.doesNotMatch(html, /Separate workflow:|not consumed by the simulated correction|separate from the simulated correction checklist/);
  }
});

test('human dispute preserves independent reading, model reading and clock provenance', () => {
  const s=state(); const report=s.evidence[1];
  report.human_observation={...report.human_observation, decision:'dispute', reading:181, normalized_kpa:null,
    flags:['human_model_reading_disagreement']};
  const html=renderEvidenceDetails(report);
  assert.match(html, /Original human observation: 181 kPa/);
  assert.match(html, /human model reading disagreement/);
  assert.match(html, /Simulated measurement time: 2026-10-27T13:00:00Z/);
  assert.match(html, /Wall-clock received: 2026-10-27T14:00:00Z/);
  const model = renderEvidenceDetails(s.evidence[0]);
  assert.match(model, /Observed numeric reading<\/dt><dd>180<\/dd>/);
  assert.match(model, /Visible unit \/ no conversion<\/dt><dd>kPa<\/dd>/);
  assert.match(html, /original model interpretation is preserved separately/i);
});

test('approved simulated correction becomes Operator primary assignment, without Commander controls', () => {
  const s=state(); s.journey.approval_current=true; s.journey.approval_id='approval-a'; s.journey.assessment.eligible=true;
  const html=renderOperator(s);
  assert.match(html, /Complete simulated filter replacement/);
  assert.doesNotMatch(html, /Record your independent observation|Approve simulated correction|Choose next observation/);
});

test('completed recovery shows outcome and preserved evidence instead of an active observation form', () => {
  const s=state(); s.journey.maintenance_status='simulated_replacement_completed';
  s.journey.recovery={status:'verified',sample_count:5,window_seconds:40,sample_refs:['sample-b']};
  const html=renderOperator(s);
  assert.match(html, /Simulated correction and recovery record/);
  assert.match(html, /Simulated operating recovery verified/);
  assert.match(html, /Shared task evidence/);
  assert.doesNotMatch(html, /Record your independent observation|Complete simulated filter replacement/);
});

test('provider-double previews are persistently labeled test output in both workspaces and inspection', () => {
  const s=state(); s.journey.test_output=true; s.evidence[0].test_output=true;
  for(const render of [renderCommander,renderOperator]) assert.match(render(s),/OFFLINE TEST OUTPUT/);
  assert.match(renderEvidenceDetails(s.evidence[0]), /No live inference, latency or token consumption/);
});
