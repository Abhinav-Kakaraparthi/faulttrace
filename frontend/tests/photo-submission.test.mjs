// Offline transport/contract tests. These do not measure NVIDIA accuracy.
import { test, after } from 'node:test';
import assert from 'node:assert/strict';
import { build } from 'vite';
import { mkdtempSync, writeFileSync, rmSync } from 'node:fs';
import { resolve, join } from 'node:path';
import { pathToFileURL } from 'node:url';

const temporary = mkdtempSync(resolve('node_modules/.photo-submission-'));
after(() => rmSync(temporary, { recursive: true, force: true }));
const output = await build({ configFile: false, logLevel: 'silent',
  build: { ssr: 'tests/presentation-entry.tsx', write: false, rollupOptions: { output: { format: 'es' } } } });
const file = join(temporary, 'render.mjs');
writeFileSync(file, output.output.find(item => item.type === 'chunk' && item.isEntry).code);
const { AccessSession, WorkflowController, renderOperator, renderCommander, renderPhotoDraft } = await import(pathToFileURL(file));
const id = '11111111-2222-4333-8444-555555555555';
const response = (value, status = 200) => new Response(JSON.stringify(value), { status });
const settle = async () => { for (let i = 0; i < 8; i++) await new Promise(resolve => setImmediate(resolve)); };
function fixture() {
  return { incident: { id: 'incident-a', revision: 3 }, task: { id: 'task-a', revision: 1, status: 'awaiting',
    asset_id: 'F-17', creation_source: 'offline provider double', instruction: 'Observe only', explanation: 'Gather evidence' },
    evidence: [], events: [], planning: [], planning_remaining: 4, inference_enabled: true,
    photo_analysis: { version: 1, contract: 'photo-observation-v1' }, photo_collection: {version: 1, assets: ['F-17', 'V-08']} };
}
async function setup({ afterUpload = () => {}, uploadError = false, analysisError = false, deferUpload } = {}) {
  const state = fixture(), writes = [];
  const transport = async (path, init) => {
    if (path === '/api/identity') return response({ profile: 'local', principal_id: null, role: null,
      capabilities: {create_incident: false}, incident_ids: [] });
    if (init.method === 'POST') {
      writes.push({path, body: init.body, headers: init.headers});
      if (path.endsWith('/images')) {
        if (deferUpload) await deferUpload;
        if (uploadError) throw new Error('offline transport interrupted');
        state.task.revision++; state.incident.revision++;
        state.evidence.push({ id, task_id: 'task-a', kind: 'image', asset_id: 'F-17', status: 'collected',
          created_at: '2026-10-30T10:00:00Z', image_url: '/ignored', origin: 'user-upload', fixture_id: null, analysis: null });
        afterUpload(state, access);
        return response({ evidence_id: id });
      }
      if (analysisError) return response({ error: 'spending_budget_exhausted' }, 429);
      return response({ analysis_id: 'analysis-a' }, 202);
    }
    if (path.endsWith('/image')) return new Response('offline-image', {headers: {'Content-Type': 'image/jpeg'}});
    return response(state);
  };
  const access = new AccessSession('local', { fetch: transport,
    upload: (path, blob, headers, signal) => transport(path, {method: 'POST', body: blob, headers: new Headers(headers), signal}),
    urls: {createObjectURL: () => 'blob:offline-image', revokeObjectURL: () => {}} });
  await access.authenticate();
  const controller = new WorkflowController(access, 60000);
  controller.start(); await settle();
  const task = controller.snapshot().state.task;
  return {access, controller, state, writes, submit: analyze => controller.submitPhoto(task,
    new Blob(['offline transport test only'], { type: 'image/jpeg' }), 'selection-a', analyze, () => {}),
    stop: () => {controller.stop(); access.logout();}};
}

test('explicit upload-and-analyze uses confirmed evidence ID and fresh task revision exactly once', async () => {
  const run = await setup();
  try {
    assert.equal(await run.submit(true), 'analysis_requested');
    assert.deepEqual(run.writes.map(x => x.path), ['/api/tasks/task-a/images', `/api/evidence/${id}/analyze-photo`]);
    assert.equal(run.writes[0].headers.get('X-Evidence-Purpose'), 'reference-photo');
    assert.deepEqual(JSON.parse(run.writes[1].body), {revision: 2});
    assert.notEqual(run.writes[0].headers.get('Idempotency-Key'), run.writes[1].headers.get('Idempotency-Key'));
    assert.equal(await run.submit(true), 'unconfirmed'); // old task revision cannot replay
    assert.equal(run.writes.length, 2);
  } finally {run.stop();}
});
test('collection-only action does not invoke analysis', async () => {
  const run = await setup();
  try { assert.equal(await run.submit(false), 'stored'); assert.equal(run.writes.length, 1); }
  finally {run.stop();}
});
test('uncertain upload never chains an analysis request or retries a write', async () => {
  const run = await setup({ uploadError: true });
  try { assert.equal(await run.submit(true), 'unconfirmed'); await settle(); assert.equal(run.writes.length, 1); }
  finally {run.stop();}
});
test('context drift, competing upload and disabled inference stop the chain after confirmed storage', async () => {
  for (const change of [s => s.task.id = 'another-task', s => s.incident.revision++,
    s => s.inference_enabled = false, s => s.photo_analysis.contract = 'unsupported',
    s => s.evidence.push({...s.evidence[0], id: 'competing-photo'})]) {
    const run = await setup({afterUpload: change});
    try {assert.equal(await run.submit(true), 'stored_analysis_stopped'); assert.equal(run.writes.length, 1);}
    finally {run.stop();}
  }
});
test('analysis allowance rejection preserves the uploaded record and never retries', async () => {
  const run = await setup({analysisError: true});
  try {
    assert.equal(await run.submit(true), 'stored_analysis_stopped'); await settle();
    assert.equal(run.writes.length, 2); assert.equal(run.state.evidence.length, 1);
    assert.match(run.controller.snapshot().error, /allowance is exhausted/);
  } finally {run.stop();}
});
test('logout during upload prevents analysis and clears private state', async () => {
  const run = await setup({afterUpload: (_s, access) => access.logout()});
  try {assert.equal(await run.submit(true), 'unconfirmed'); assert.equal(run.writes.length, 1); assert.equal(run.controller.snapshot().state, null);}
  finally {run.stop();}
});
test('a second click cannot start a competing upload while the first is pending', async () => {
  let release; const deferred = new Promise(done => {release = done;});
  const run = await setup({deferUpload: deferred});
  try {
    const first = run.submit(true); await settle();
    assert.equal(await run.submit(true), 'unconfirmed'); release();
    assert.equal(await first, 'analysis_requested'); assert.equal(run.writes.length, 2);
  } finally {release(); run.stop();}
});
test('legacy display results cannot be offered as confirmable photographs', () => {
  const state = fixture();
  state.journey = {evidence_mode: 'task-evidence', maintenance_status: 'not_completed', observations: [], samples: [],
    assessment: {eligible: false, blockers: [], evidence_refs: [], alternatives: []}, policy: {}, recovery: {status: 'not_started'}};
  state.evidence = [{id, task_id: 'task-a', kind: 'image', asset_id: 'F-17', status: 'accepted', origin: 'synthetic-fixture',
    fixture_id: 'panel-a', created_at: '2026-10-30T10:00:00Z', image_url: '/offline', analysis: {status: 'interpreted',
      interpretation: {readability: 'readable', reading: 180, unit: 'kPa', evidence_ref: `evidence-${id}`}}}];
  const html = renderOperator(state, {release: true});
  assert.match(html, /value="confirm" disabled=""/);
  assert.match(html, /legacy contract and cannot be confirmed/);
  assert.doesNotMatch(html, /fixture-development/);
  assert.match(html, /Real photograph examples and credits/);
  assert.match(html, /not from this simulated plant/);
  assert.match(renderPhotoDraft({onAnalyze: () => {}}), /Upload and analyze with NVIDIA/);
});

test('guided continuation consent is a Commander control and disables competing manual planning', () => {
  const state = fixture();
  state.journey = {evidence_mode:'task-evidence', maintenance_status:'not_completed', observations:[], samples:[],
    assessment:{eligible:false,blockers:[],evidence_refs:[],alternatives:[]},policy:{},recovery:{status:'not_started'}};
  state.continuation = {version:1,enabled:false,phase:'idle',expires:null,error:null};
  state.journey.policy = {restriction_pressure_kpa:[170,195],restricted_flow_m3h:[80,95],
    recovery_flow_m3h:[115,125],recovery_pressure_kpa:[25,40],valve_feedback_percent:[65,80]};
  assert.match(renderCommander(state), /Start guided investigation/);
  assert.doesNotMatch(renderOperator(state), /Start guided investigation|Pause guided investigation/);
  state.continuation = {...state.continuation,enabled:true,phase:'awaiting_field_evidence'};
  assert.match(renderCommander(state), /Pause guided investigation/);
  assert.match(renderCommander(state), /Waiting for Operator to return field evidence/);
  assert.match(renderCommander(state), /<button[^>]*disabled[^>]*>Choose next observation/);
  assert.match(renderCommander(state), /No automatic retries, approvals or equipment actions/);
});
