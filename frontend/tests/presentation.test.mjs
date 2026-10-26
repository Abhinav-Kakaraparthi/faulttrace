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
const { renderJourney, renderEvidence, renderPlanningHistory, renderAudit, renderCommander, renderOperator, renderPhotoCapture, renderPhotoDraft, renderEvidenceDetails } = await import(pathToFileURL(file));

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
  for (const heading of operator.matchAll(/<h2[^>]*>([\s\S]*?)<\/h2>/g)) assert.doesNotMatch(heading[1], /<section|<input|<fieldset/);
  assert.ok(operator.indexOf('Photograph the assigned observation') > operator.indexOf('Read the assigned local indicator only'));
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


test('assigned camera collection also offers ordinary files and capability-gates older servers', () => {
  const html=renderPhotoCapture();
  const inputs=html.match(/<input[^>]*type="file"[^>]*>/g);
  assert.equal(inputs.length,2);
  assert.equal(inputs.filter(input=>input.includes('capture="environment"')).length,1);
  assert.match(html,/Take a photograph/);assert.match(html,/Choose a photograph from files/);
  assert.match(html,/assignment does not identify/i);assert.match(html,/ordinary pressure gauge does not establish differential pressure/i);
  assert.match(html,/valve handle image does not prove internal valve condition/i);
  assert.doesNotMatch(html,/<img/);
  const old=renderPhotoCapture(false);
  assert.match(old,/requires the updated backend/);
  assert.equal((old.match(/<input[^>]*disabled/g)||[]).length,2);
});
test('draft displays selected local photo, replace/cancel controls and honest progress states', () => {
  const draft=renderPhotoDraft();
  assert.match(draft,/src="blob:actual-local-selection"/);
  assert.match(draft,/not submitted/);assert.match(draft,/Replace photograph/);assert.match(draft,/Cancel selection/);
  const busy=renderPhotoDraft({busy:true,progress:37});
  assert.match(busy,/Uploading 37%/);assert.match(busy,/<progress[^>]*value="37"/);
  assert.match(busy,/<button[^>]*disabled[^>]*>Replace photograph/);
  assert.match(renderPhotoDraft({busy:true,progress:100}),/waiting for server validation and storage/);
  assert.match(renderPhotoDraft({disabled:true}), /<button[^>]*disabled[^>]*>Replace photograph/);
  assert.match(renderPhotoDraft({failed:true}),/<button[^>]*disabled[^>]*>Submit image \/ collection only/);
});
test('stored photograph, assigned asset, human reports and NVIDIA interpretation remain distinct', () => {
  const state=imageTaskState();state.photo_collection={version:1,assets:['F-17','V-08']};
  const photo={...state.evidence[0],status:'collected',asset_id:'V-08',image_url:'/api/evidence/photo-id/image'};
  state.evidence=[photo];
  for(const html of [renderOperator(state),renderCommander(state),renderEvidenceDetails(photo)]) {
    assert.match(html,/src="\/api\/evidence\/photo-id\/image"/);
    assert.match(html,/identity.*not assessed|identity.*not established/i);
    assert.match(html,/collection.only/i);
    assert.doesNotMatch(html,/>Analyze image</);
  }
  const human={...photo,id:'human-report',kind:'report',status:'accepted',report:'intermediate',origin:'human-report',image_url:null};
  state.evidence.push(human);
  assert.match(renderEvidence(state),/Human report \/ intermediate/);
  assert.doesNotMatch(renderEvidenceDetails(human),/src="\/api\/evidence/);
  assert.match(renderEvidenceDetails(human),/NVIDIA readability \(if analyzed\).*Not analyzed/);
});


test('photo analysis is explicit, capability/opt-in gated and separate from fixture analysis', () => {
  const state=imageTaskState();state.evidence[0]={...state.evidence[0],status:'collected',asset_id:'F-17',image_url:'/api/evidence/photo/image'};
  state.photo_analysis={version:1,contract:'photo-observation-v1'};
  let html=renderOperator(state);
  assert.match(html,/>Analyze photographic observation</);
  assert.doesNotMatch(html,/>Analyze image</);
  assert.doesNotMatch(renderCommander(state),/>Analyze photographic observation</);
  state.inference_enabled=false;
  assert.match(renderOperator(state),/<button[^>]*disabled[^>]*>Analyze photographic observation</);
  state.inference_enabled=true;delete state.photo_analysis;
  assert.match(renderOperator(state),/<button[^>]*disabled[^>]*>Analyze photographic observation</);
  assert.match(renderOperator(state),/requires an updated backend/);
});

function photoResult(changes={}) {
  return {category:'gauge',readability:'readable',measurement_type:'indeterminate',visible_unit:'PSI',reading:75,
    label_text:'PG-21',valve_orientation:'not_applicable',reasons:['measurement_type_uncertain'],evidence_ref:'evidence-photo',...changes};
}
function analyzedPhoto(value,status='interpreted') {
  const state=imageTaskState();
  state.evidence[0]={...state.evidence[0],status:'collected',asset_id:'V-08',image_url:'/api/evidence/photo/image',
    analysis:{id:'photo-attempt',contract:'photo-observation-v1',status,interpretation:value,
      receipt:{...{},usage_status:'partial',validation_result:'passed',token_usage:{prompt_tokens:11,completion_tokens:null,total_tokens:null}},accounting:'recorded'}};
  return state;
}

test('both workspaces preserve actual gauge values/units, unknown type, uncertainty and provenance without scenario defaults', () => {
  const state=analyzedPhoto(photoResult());
  for(const html of [renderOperator(state),renderCommander(state),renderEvidenceDetails(state.evidence[0])]) {
    assert.match(html,/src="\/api\/evidence\/photo\/image"/);
    assert.match(html,/Observed numeric reading/);assert.match(html,/>75</);
    assert.match(html,/>PSI</);assert.match(html,/>indeterminate</);
    assert.match(html,/Measurement type cannot be established/);
    assert.match(html,/PG-21/);assert.match(html,/not.*compatibility check/);
    assert.match(html,/excluded from incident pressure comparisons/i);
    assert.doesNotMatch(html,/180 kPa|75 kPa/);
  }
  const ledger=renderOperator(state);
  assert.match(ledger,/output unknown/);
  assert.match(ledger,/Usage partial/);
  assert.match(ledger,/Ledger recorded/);
});

test('valve label remains distinct from assignment and instructions are escaped, not equipment authorization', () => {
  const state=analyzedPhoto(photoResult({category:'valve',measurement_type:'not_applicable',visible_unit:null,reading:null,
    label_text:'BV-104 <script>IGNORE POLICY</script>',valve_orientation:'perpendicular_to_visible_pipe',reasons:[]}));
  const html=renderOperator(state);
  assert.match(html,/Assigned asset: V-08/);
  assert.match(html,/BV-104 &lt;script&gt;IGNORE POLICY&lt;\/script&gt;/);
  assert.match(html,/perpendicular to visible pipe/);
  assert.match(html,/does not prove internal valve position or operating condition/);
  assert.doesNotMatch(html,/<script>|internal valve.*closed/);
  assert.doesNotMatch(html,/>Analyze photographic observation</);
});

test('ambiguous/unreadable/unrelated observations remain bounded results, with failed/stale/uncertain status visible', () => {
  for(const [category,readability,reasons] of [['gauge','readable',['ambiguous_scale']],['cannot-determine','unreadable',['category_uncertain']],['other','readable',['not_equipment']]]) {
    const state=analyzedPhoto(photoResult({category,readability,measurement_type:category==='gauge'?'pressure':'not_applicable',reading:null,visible_unit:null,reasons}));
    const html=renderOperator(state);
    assert.match(html,/Not established; no number inferred/);
    assert.match(html,new RegExp(`>${category}<`));
    assert.doesNotMatch(html,/180 kPa/);
  }
  for(const status of ['failed','stale','uncertain']) {
    const state=analyzedPhoto(photoResult(),status);
    const html=renderOperator(state);
    assert.match(html,new RegExp(`Photographic analysis / ${status}`));
    assert.match(html,/not an accepted current observation/);
  }
});
