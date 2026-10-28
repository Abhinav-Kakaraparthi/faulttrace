// Real frontend cookie/session/access code against real ASGI, not browser acceptance.
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { createInterface } from 'node:readline';
import { mkdtempSync, readFileSync, writeFileSync } from 'node:fs';
import { resolve, join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { build } from 'vite';
const output = await build({ configFile: false, logLevel: 'silent', build: {
  ssr: 'tests/combined-entry.ts', write: false, rollupOptions: { output: { format: 'es' } } } });
const folder = mkdtempSync(resolve('node_modules/.demo-contract-'));
const file = join(folder, 'entry.mjs');
writeFileSync(file, output.output.find(item => item.type === 'chunk' && item.isEntry).code);
const { AccessSession, WorkflowController, demoSessionRequest } = await import(pathToFileURL(file));
const env = { ...process.env, FAULTTRACE_ALLOW_INFERENCE: '0' }; delete env.NEBIUS_API_KEY;
const child = spawn(process.env.FAULTTRACE_TEST_PYTHON || 'python', ['-B', 'tools/demo_contract_peer.py'],
  { cwd: resolve('..'), env, stdio: ['pipe','pipe','pipe'] });
child.stderr.resume();
let sequence = 0;
const pending = new Map();
const lines = createInterface({ input: child.stdout });
lines.on('line', line => {
  const value = JSON.parse(line), waiter = pending.get(value.id);
  if (waiter) { pending.delete(value.id); value.error ? waiter.reject(new Error('Demo peer failure')) : waiter.resolve(value.result); }
});
child.on('exit', () => { for (const item of pending.values()) item.reject(new Error('Demo peer exited')); pending.clear(); });
const ask = (action, values = {}) => new Promise((resolve, reject) => {
  const id = ++sequence; pending.set(id, { resolve, reject });
  child.stdin.write(JSON.stringify({ id, action, ...values }) + '\n');
});
function browser() {
  let cookie = '';
  return async (path, init) => {
    assert.equal(init.credentials, 'same-origin');
    const headers = new Headers(init.headers);
    assert.equal(headers.has('Authorization'), false);
    if (cookie) headers.set('Cookie', cookie);
    if (init.method === 'POST') headers.set('Origin', 'http://127.0.0.1:5211');
    const body = init.body instanceof Blob ? Buffer.from(await init.body.arrayBuffer()) : Buffer.from(init.body ?? '');
    const value = await ask('request', { method: init.method || 'GET', path,
      headers: Object.fromEntries(headers), body: body.toString('base64') });
    if (value.headers['set-cookie']) cookie = value.headers['set-cookie'].includes('Max-Age=0') ? '' : value.headers['set-cookie'].split(';')[0];
    return new Response(Buffer.from(value.body, 'base64'), { status: value.status, headers: value.headers });
  };
}
const original = globalThis.fetch;
const fetchA = browser(), fetchB = browser();
const sessions = [];
const makeAccess = async (meta, workspace, fetch) => {
  const access = new AccessSession('demo', { fetch, demo: { workspace, run: meta.active_run, csrf: meta.csrf_token },
    urls: { createObjectURL: () => 'blob:demo-test', revokeObjectURL: () => {} } });
  assert.equal(await access.authenticate(), true); sessions.push(access); return access;
};
try {
  globalThis.fetch = fetchA;
  let a = await demoSessionRequest(); assert.equal(a.active_run, null);
  a = await demoSessionRequest('start', a, crypto.randomUUID());
  const chief = await makeAccess(a, 'commander', fetchA);
  const field = await makeAccess(a, 'operator', fetchA); // Separate tab, same browser cookie.
  let state = await field.state(new AbortController().signal);
  const incident = state.incident.id, task = state.task.id;
  assert.equal(chief.snapshot().identity.profile, 'demo');
  assert.ok(chief.snapshot().identity.incident_ids.includes(incident));
  assert.equal(state.inference_enabled, false);
  assert.ok(state.task.creation_source.includes('not NVIDIA-generated'));
  const refreshed = await demoSessionRequest(); assert.equal(refreshed.active_run, a.active_run);
  const reopened = await makeAccess(refreshed, 'operator', fetchA);
  assert.equal((await reopened.state(new AbortController().signal)).task.id, task);
  const bytes = readFileSync(resolve('../fixtures/image-evidence/panel-a.png'));
  await field.mutate(`/api/tasks/${task}/images`, new Blob([bytes], { type: 'image/png' }), crypto.randomUUID(),
    { 'X-Task-Revision': '1', 'X-Evidence-Purpose': 'reference-photo' });
  state = await chief.state(new AbortController().signal);
  const photo = state.evidence[0]; assert.equal(photo.image_url, 'blob:demo-test');
  await assert.rejects(chief.mutate(`/api/evidence/${photo.id}/analyze-photo`, { revision: 2 }, crypto.randomUUID()),
    error => error.code === 'inference_disabled');
  globalThis.fetch = fetchB;
  let b = await demoSessionRequest(); b = await demoSessionRequest('start', b, crypto.randomUUID());
  const outsider = await makeAccess(b, 'operator', fetchB);
  assert.equal((await outsider.state(new AbortController().signal)).evidence.length, 0);
  await assert.rejects(outsider.json(`/api/evidence/${photo.id}/image`), error => error.code === 'access_denied');
  globalThis.fetch = fetchA;
  const next = await demoSessionRequest('restart', a, crypto.randomUUID());
  await assert.rejects(field.state(new AbortController().signal));
  assert.equal(field.snapshot().status, 'locked'); // Old tab/run cannot retarget a mutation.
  const fresh = await makeAccess(next, 'operator', fetchA);
  assert.notEqual((await fresh.state(new AbortController().signal)).incident.id, incident);
  await ask('expire'); await assert.rejects(fresh.state(new AbortController().signal));
  assert.equal(fresh.snapshot().status, 'locked'); assert.ok(!fresh.snapshot().message.includes('token'));
  const summary = await ask('summary');
  assert.equal(summary.forbidden_external_attempts, 0); assert.equal(summary.ledger_files, 0);
  assert.equal(summary.runs, 3);
  console.log('PASS: one-click session, cookie refresh/second tab, automatic assignments, upload/image isolation, restart stale-tab denial and expiry');
  console.log('No provider calls or model output; browser cookie behavior still needs manual acceptance');
} finally {
  globalThis.fetch = original; sessions.forEach(access => access.logout());
  child.stdin.write(JSON.stringify({ id: ++sequence, action: 'close' }) + '\n'); child.stdin.end();
  const timeout = setTimeout(() => child.kill(), 3000);
  await new Promise(done => { if (child.exitCode !== null) done(); else child.once('exit', done); });
  clearTimeout(timeout); lines.close();
}
