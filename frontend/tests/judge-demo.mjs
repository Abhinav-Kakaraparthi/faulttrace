import { test } from 'node:test';
import assert from 'node:assert/strict';

export function registerJudgeDemoTests({ renderDemoEntry, renderCommander, renderOperator, imageTaskState,
    demoSessionRequest, AccessSession, validateIdentity }) {
  const run = '11111111-2222-4333-8444-555555555555';
  const meta = { active_run: null, csrf_token: 'c'.repeat(43), expires_at: 9999999999,
    inference_enabled: false, privileges: 'One demo visitor uses both workspaces.' };
  const response = (value, status = 200) => new Response(JSON.stringify(value), { status });
  test('judge entry offers Try demo without token/account fields and discloses visitor privileges and disabled inference', () => {
    const html = renderDemoEntry();
    assert.match(html, />Try demo</); assert.doesNotMatch(html, /<input|<form|Bearer /);
    assert.match(html, /not production separation between employees/);
    assert.match(html, /NVIDIA inference is disabled/); assert.match(html, /without deleting history/);
  });
  test('cookie bootstrap is shared in flight; mutation carries CSRF/run/UUID and no browser bearer', async () => {
    const original = globalThis.fetch; const calls = []; let finish;
    globalThis.fetch = (path, init) => { calls.push({ path, init }); return new Promise(done => { finish = done; }); };
    try {
      const first = demoSessionRequest(), second = demoSessionRequest();
      assert.equal(first, second); assert.equal(calls.length, 1);
      finish(response(meta)); const value = await first;
      globalThis.fetch = async (path, init) => { calls.push({ path, init }); return response({ ...meta, active_run: run }); };
      const key = crypto.randomUUID(); await demoSessionRequest('start', value, key);
      const request = calls[1]; assert.equal(request.init.credentials, 'same-origin');
      const headers = new Headers(request.init.headers);
      assert.equal(headers.get('X-CSRF-Token'), meta.csrf_token); assert.equal(headers.get('Idempotency-Key'), key);
      assert.equal(headers.get('Authorization'), null); assert.equal(request.init.body, '{}');
    } finally { globalThis.fetch = original; }
  });
  test('demo access uses cookie credentials and workspace/run headers for state and writes; stale run clears memory', async () => {
    const identity = { profile: 'demo', principal_id: 'demo-operator', role: 'operator',
      capabilities: { create_incident: false }, incident_ids: [run] };
    const calls = []; let stale = false;
    const access = new AccessSession('demo', { demo: { workspace: 'operator', run, csrf: meta.csrf_token },
      fetch: async (path, init) => { calls.push({ path, init }); return path === '/api/identity' ? response(identity) :
        stale ? response({ error: 'demo_session_changed' }, 409) : response({ ok: true }); } });
    assert.equal(await access.authenticate(), true);
    await access.mutate('/api/tasks/task/reports', { revision: 1, report: 'cannot-access' }, crypto.randomUUID());
    const request = calls.at(-1); assert.equal(request.init.credentials, 'same-origin');
    assert.equal(request.init.headers.get('X-FaultTrace-Workspace'), 'operator');
    assert.equal(request.init.headers.get('X-FaultTrace-Demo-Run'), run);
    assert.equal(request.init.headers.get('X-CSRF-Token'), meta.csrf_token);
    assert.equal(request.init.headers.get('Authorization'), null);
    stale = true; await assert.rejects(access.json('/api/state'));
    assert.equal(access.snapshot().status, 'locked'); assert.equal(access.snapshot().identity, null);
    assert.throws(() => validateIdentity({ ...identity, capabilities: { create_incident: true } }, 'demo'));
  });
  test('demo templates stay Commander-only, distinct from NVIDIA and blocked by pending task', () => {
    const state = imageTaskState();
    state.demo = { template_actions: ['OBSERVE_V-08_OBSERVE_POSITION'], assignment_remaining: 3 };
    const commander = renderCommander(state), operator = renderOperator(state);
    assert.match(commander, /Demo observation templates — no AI inference/);
    assert.match(commander, /not NVIDIA choices/);
    assert.match(commander, /<button[^>]*disabled[^>]*>Assign V-08 observation/);
    assert.doesNotMatch(operator, /Assign V-08 observation/);
  });
  test('invalid session metadata fails without logging or reflecting its values', async () => {
    const original = globalThis.fetch;
    try {
      globalThis.fetch = async () => response({ ...meta, inference_enabled: true, csrf_token: 'PRIVATE_SENTINEL' });
      await assert.rejects(demoSessionRequest(), error => !error.message.includes('PRIVATE_SENTINEL'));
    } finally { globalThis.fetch = original; }
  });
}
