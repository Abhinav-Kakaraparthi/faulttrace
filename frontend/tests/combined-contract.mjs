// Actual frontend classes + real release ASGI API, no HTTP listener or provider.
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { createInterface } from 'node:readline';
import { mkdtempSync, readFileSync, writeFileSync } from 'node:fs';
import { resolve, join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { build } from 'vite';

const output = await build({ configFile: false, logLevel: 'silent', build: {
  ssr: 'tests/combined-entry.ts', write: false, rollupOptions: { output: { format: 'es' } } } });
const directory = mkdtempSync(resolve('node_modules/.combined-contract-'));
const entry = join(directory, 'entry.mjs');
writeFileSync(entry, output.output.find(item => item.type === 'chunk' && item.isEntry).code);
const { AccessSession, WorkflowController } = await import(pathToFileURL(entry));
const env = { ...process.env, FAULTTRACE_ALLOW_INFERENCE: '0' }; delete env.NEBIUS_API_KEY;
const child = spawn(process.env.FAULTTRACE_TEST_PYTHON || 'python',
  ['-B', 'tools/combined_contract_peer.py'], { cwd: resolve('..'), env, stdio: ['pipe', 'pipe', 'pipe'] });
// Do not echo child stderr, protocol responses, credentials or request headers.
child.stderr.resume();
const pending = new Map(); let sequence = 0;
const lines = createInterface({ input: child.stdout });
lines.on('line', line => {
  const value = JSON.parse(line); const waiter = pending.get(value.id);
  if (waiter) { pending.delete(value.id); value.error ? waiter.reject(new Error('ASGI peer failed')) : waiter.resolve(value.result); }
});
child.on('exit', () => { for (const item of pending.values()) item.reject(new Error('ASGI peer exited')); pending.clear(); });
const ask = (action, fields = {}) => new Promise((resolve, reject) => {
  const id = ++sequence; pending.set(id, { resolve, reject });
  child.stdin.write(JSON.stringify({ id, action, ...fields }) + '\n');
});
let held = null;
const transport = async (path, init) => {
  const body = init.body instanceof Blob ? Buffer.from(await init.body.arrayBuffer()) : Buffer.from(init.body ?? '');
  const value = await ask('request', { method: init.method || 'GET', path,
    headers: Object.fromEntries(init.headers), body: body.toString('base64') });
  const response = new Response(Buffer.from(value.body, 'base64'), { status: value.status, headers: value.headers });
  if (held && path === '/api/state') { held.ready(); await held.promise; held = null; }
  return response;
};
const revoked = [];
let urls = 0;
const session = () => new AccessSession('release', { fetch: transport,
  upload: (path, blob, headers, signal) => transport(path, {method: 'POST', body: blob, headers: new Headers(headers), signal}), urls: {
  createObjectURL: () => `blob:combined-${++urls}`, revokeObjectURL: value => revoked.push(value) } });
const wait = async predicate => {
  const until = Date.now() + 8000;
  while (!predicate()) { if (Date.now() > until) throw new Error('Contract state timeout'); await new Promise(done => setTimeout(done, 10)); }
};
let commander, operator, chief, field;
try {
  const tokens = await ask('identities'); chief = session(); field = session();
  assert.equal(await chief.authenticate(tokens.chief), true);
  assert.deepEqual(chief.snapshot().identity.incident_ids, []);
  commander = new WorkflowController(chief); commander.start();
  await wait(() => commander.snapshot().connection === 'online');
  assert.equal(commander.snapshot().state.incident, null);
  assert.equal(await commander.mutate('/api/investigations', {}, 'create'), true);
  const incident = chief.snapshot().identity.incident_ids[0]; assert.ok(incident);
  commander.stop(); commander = new WorkflowController(chief); commander.start();
  await wait(() => commander.snapshot().state?.incident.id === incident);
  assert.equal(await field.authenticate(tokens.field), true);
  operator = new WorkflowController(field); operator.start();
  await wait(() => operator.snapshot().denied);
  const assignment = await ask('assign', { incident });
  assert.equal(await field.refreshIdentity(), true);
  operator.stop(); operator = new WorkflowController(field); operator.start();
  await wait(() => operator.snapshot().state?.task?.id === assignment.task_id);
  assert.equal(operator.snapshot().state.task.creation_source, 'TEST-CREATED / no model request');
  const bytes = readFileSync(resolve('../fixtures/image-evidence/panel-a.png'));
  assert.equal(await operator.submitPhoto(operator.snapshot().state.task,
    new Blob([bytes], { type: 'image/png' }), 'upload', false, () => {}), 'stored');
  await wait(() => operator.snapshot().state.evidence.length === 1);
  const photo = operator.snapshot().state.evidence[0];
  assert.ok(photo.image_url.startsWith('blob:combined-'));
  assert.equal(photo.origin, 'user-upload'); assert.equal(photo.fixture_id, null);
  operator.inspect(photo.id); assert.equal(operator.snapshot().inspectionId, photo.id);
  commander.refresh(); await wait(() => commander.snapshot().state.evidence.length === 1);
  assert.ok(commander.snapshot().state.evidence[0].image_url.startsWith('blob:combined-'));
  assert.equal(await operator.mutate(`/api/evidence/${photo.id}/analyze-photo`, { revision: 2 }, 'analysis'), false);
  assert.equal(field.snapshot().status, 'ready'); assert.equal(operator.snapshot().denied, false);
  assert.equal(operator.snapshot().inspectionId, photo.id);
  assert.equal(await operator.mutate(`/api/tasks/${assignment.task_id}/reports`,
    { revision: 2, report: 'cannot-access' }, 'refusal'), true);
  await wait(() => operator.snapshot().state.evidence.length === 2);
  const report = operator.snapshot().state.evidence.at(-1);
  assert.equal(report.report, 'cannot-access'); operator.inspect(report.id);
  await ask('grant', { incident, allow: false }); operator.refresh();
  await wait(() => operator.snapshot().denied);
  assert.equal(operator.snapshot().state, null); assert.equal(operator.snapshot().inspectionId, null);
  assert.equal(field.snapshot().status, 'ready'); assert.ok(revoked.length > 0);
  await ask('grant', { incident, allow: true }); operator.refresh();
  await wait(() => operator.snapshot().state?.evidence.length === 2);
  assert.equal(operator.snapshot().inspectionId, null);
  let release, started;
  const startedPromise = new Promise(done => { started = done; });
  held = { ready: started, promise: new Promise(done => { release = done; }) };
  operator.refresh(); await startedPromise; field.logout(); release();
  await new Promise(done => setTimeout(done, 30));
  assert.equal(field.snapshot().status, 'locked'); assert.equal(operator.snapshot().state, null);
  assert.equal(operator.snapshot().inspectionId, null);
  assert.equal(await field.authenticate(tokens.field), true);
  assert.equal(operator.snapshot().state, null); // No old-controller/write replay.
  const summary = await ask('summary');
  assert.deepEqual(summary, { incidents: 1, tasks: 1, planning: 0, analyses: 0,
    provider_calls: 0, forbidden_network: 0 });
  console.log('PASS: real identity, creation/grants, assigned upload/image, refusal, application 403, access denial/inspection, restoration and logout isolation');
  console.log('Provider calls: 0; forbidden external attempts: 0; browser acceptance: not tested');
} finally {
  commander?.stop(); operator?.stop(); chief?.logout(); field?.logout();
  child.stdin.write(JSON.stringify({ id: ++sequence, action: 'close' }) + '\n');
  child.stdin.end();
  const timeout = setTimeout(() => child.kill(), 3000);
  await new Promise(done => { if (child.exitCode !== null) done(); else child.once('exit', done); });
  clearTimeout(timeout); lines.close();
}
