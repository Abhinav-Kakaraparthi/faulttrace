// Offline, independently expected bearer-contract outcomes. Not combined API or browser acceptance.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

export function registerAuthenticationTests(harness) {
  const { AccessSession, WorkflowController, configuredProfile, validateIdentity, canCreate, workspaceAllowed,
    renderLocked, renderTokenEntry, renderWrongWorkspace, renderCommander, renderOperator, snapshot, imageTaskState } = harness;
  const incident = '11111111-2222-4333-8444-555555555555';
  const key = 'aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee';
  const identity = (role = 'operator', create = false) => ({ profile: 'release', principal_id: `${role}-review`, role,
    capabilities: { create_incident: create }, incident_ids: [incident] });
  const local = { profile: 'local', principal_id: null, role: null, capabilities: { create_incident: false }, incident_ids: [] };
  const state = (evidence = []) => ({ incident: { id: incident, revision: 7 }, task: null, evidence,
    planning: [], events: [], planning_remaining: 4, inference_enabled: false });
  const photo = id => ({ id, kind: 'image', task_id: 'task-a', image_url: 'https://untrusted.invalid/leak', asset_id: 'F-17' });
  const response = (value, status = 200) => new Response(JSON.stringify(value), { status });
  const deferred = () => { let resolve; const promise = new Promise(done => { resolve = done; }); return { promise, resolve }; };
  const settle = async () => { for (let i = 0; i < 12; i++) await new Promise(resolve => setImmediate(resolve)); };
  const setup = (handler, profile = 'release', extra = {}) => {
    const calls = [];
    const access = new AccessSession(profile, { fetch: async (path, init) => {
      calls.push({ path, init }); return handler(path, init);
    }, ...extra });
    return { access, calls };
  };

  test('release is default; explicit local requires its exact identity; failures never downgrade', async () => {
    assert.equal(configuredProfile(undefined), 'release'); assert.equal(configuredProfile(''), 'release');
    assert.equal(configuredProfile('release'), 'release'); assert.equal(configuredProfile('local'), 'local');
    assert.throws(() => configuredProfile('LOCAL'));
    for (const value of [null, {}, local, { ...identity(), role: 'admin' }, { ...identity(), capabilities: {} },
      { ...identity(), capabilities: { create_incident: true } }, { ...identity(), incident_ids: ['bad'] },
      { ...identity(), expiry: 123 }, { ...identity(), profile: 'local' }, { ...identity(), incident_ids: [incident, incident] }]) {
      assert.throws(() => validateIdentity(value, 'release'));
    }
    assert.deepEqual(validateIdentity(local, 'local'), local);
    assert.throws(() => validateIdentity(identity(), 'local'));
    for (const reply of [() => response({}, 404), () => response({}, 500), () => response(local),
      () => response({}, 401), () => { throw new Error('network failure'); }]) {
      const { access, calls } = setup(reply);
      assert.equal(await access.authenticate('SYNTHETIC_TEST_CREDENTIAL'), false);
      assert.equal(access.snapshot().status, 'locked'); assert.equal(access.snapshot().identity, null);
      assert.deepEqual(calls.map(call => call.path), ['/api/identity']);
    }
    const { access, calls } = setup(() => response(local), 'local');
    assert.equal(await access.authenticate(), true);
    assert.equal(calls[0].init.headers.has('Authorization'), false);
    await access.mutate('/api/incidents', {}, key);
    assert.equal(calls[1].init.headers.get('X-FaultTrace-Local'), '1');
    access.logout();
  });

  test('identity is mandatory before private reads; server role/capability determines allowed workspaces', async () => {
    const { access, calls } = setup(() => response(identity('commander', false)));
    await assert.rejects(access.json('/api/state')); assert.equal(calls.length, 0);
    assert.equal(await access.authenticate('SYNTHETIC_TEST_CREDENTIAL'), true);
    assert.equal(canCreate(access.snapshot().identity), false);
    assert.equal(workspaceAllowed(access.snapshot().identity, 'commander'), true);
    assert.equal(workspaceAllowed(access.snapshot().identity, 'operator'), false);
    assert.equal(canCreate(identity('commander', true)), true); assert.equal(canCreate(identity()), false);
    assert.equal(canCreate(local), true); assert.equal(workspaceAllowed(local, 'operator'), true);
    access.logout();
  });

  test('every JSON mutation and poll carries bearer authentication and preserved bodies/UUID headers', async () => {
    const { access, calls } = setup(path => response(path === '/api/identity' ? identity('commander', true) : state()));
    await access.authenticate('SYNTHETIC_TEST_CREDENTIAL');
    await access.state(new AbortController().signal);
    const routes = ['/api/incidents', '/api/investigations', '/api/simulation/start', '/api/planning',
      '/api/simulation/advance', '/api/simulation/approve', '/api/simulation/execute', '/api/tasks/task-a/observations',
      '/api/tasks/task-a/reports', '/api/tasks/task-a/reopen', '/api/tasks/task-a/photo-follow-up',
      '/api/evidence/photo-a/analyze', '/api/evidence/photo-a/analyze-photo'];
    for (const path of routes) await access.mutate(path, { revision: 7, sentinel: 'unchanged-contract-body' }, key);
    for (const { path, init } of calls) {
      assert.equal(init.headers.get('Authorization'), 'Bearer SYNTHETIC_TEST_CREDENTIAL', path);
      assert.equal(init.headers.has('X-FaultTrace-Local'), false); assert.equal(init.cache, 'no-store');
      assert.equal(init.credentials, 'omit'); assert.equal(init.redirect, 'error');
      assert.doesNotMatch(path, /SYNTHETIC_TEST_CREDENTIAL|\?/);
      if (init.method === 'POST') {
        assert.equal(init.headers.get('Content-Type'), 'application/json'); assert.equal(init.headers.get('Idempotency-Key'), key);
        assert.deepEqual(JSON.parse(init.body), { revision: 7, sentinel: 'unchanged-contract-body' });
      }
    }
    access.logout();
  });

  test('XHR reference photo and fetch fixture uploads preserve distinct purpose, revision, bytes and 2 MiB limit', async () => {
    const uploads = [], progress = [];
    const { access, calls } = setup(() => response(identity()), 'release', { upload: async (...args) => {
      uploads.push(args); args[4](30); args[4](100); return response({ evidence_id: 'photo-a' });
    } });
    await access.authenticate('SYNTHETIC_TEST_CREDENTIAL');
    const blob = new Blob(['synthetic-image-bytes'], { type: 'image/png' });
    await access.mutate('/api/tasks/task-a/images', blob, key, { 'X-Task-Revision': '7', 'X-Evidence-Purpose': 'reference-photo' }, value => progress.push(value));
    assert.equal(uploads.length, 1); assert.equal(uploads[0][1], blob);
    const headers = new Headers(uploads[0][2]);
    assert.equal(headers.get('Authorization'), 'Bearer SYNTHETIC_TEST_CREDENTIAL');
    assert.equal(headers.get('Idempotency-Key'), key); assert.equal(headers.get('Content-Type'), 'image/png');
    assert.equal(headers.get('X-Task-Revision'), '7'); assert.equal(headers.get('X-Evidence-Purpose'), 'reference-photo');
    assert.equal(headers.has('X-Fixture-Id'), false); assert.equal(headers.has('X-FaultTrace-Local'), false);
    assert.deepEqual(progress, [30, 100]);
    await access.mutate('/api/tasks/task-a/images', blob, key, { 'X-Task-Revision': '7', 'X-Fixture-Id': 'panel-a' });
    assert.equal(calls.at(-1).init.body, blob); assert.equal(calls.at(-1).init.headers.get('X-Fixture-Id'), 'panel-a');
    assert.equal(calls.at(-1).init.headers.has('X-Evidence-Purpose'), false);
    await assert.rejects(access.mutate('/api/tasks/task-a/images', new Blob([new Uint8Array(2097153)], { type: 'image/png' }), key));
    await assert.rejects(access.mutate('/api/tasks/task-a/images', blob, 'noncanonical-key'));
    assert.equal(uploads.length, 1); access.logout();
  });

  test('application 403/conflicts/internal errors preserve identity; only 401 clears access', async () => {
    let result = response({ error: 'inference_disabled' }, 403);
    const { access } = setup(path => path === '/api/identity' ? response(identity()) : result);
    await access.authenticate('SYNTHETIC_TEST_CREDENTIAL');
    for (const [status, code] of [[403, 'inference_disabled'], [403, 'access_denied'], [409, 'stale_task'], [409, 'idempotency_conflict'], [500, 'storage_or_internal_failure']]) {
      result = response({ error: code }, status);
      await assert.rejects(access.json('/api/state'), error => error.status === status && error.code === code);
      assert.equal(access.snapshot().status, 'ready');
    }
    result = response({ error: 'authentication_required' }, 401);
    await assert.rejects(access.json('/api/state')); assert.equal(access.snapshot().status, 'locked');
    assert.equal(access.snapshot().identity, null);
  });

  test('protected image bytes use bearer fetch, shared temporary blobs, replacement and logout revocation', async () => {
    let images = [photo('photo-a')]; const created = [], revoked = [];
    const { access, calls } = setup(path => path === '/api/identity' ? response(identity()) : path === '/api/state' ? response(state(images)) : new Response('image-bytes', { headers: { 'Content-Type': 'image/png' } }),
      'release', { urls: { createObjectURL: () => { const url = `blob:test-${created.length}`; created.push(url); return url; }, revokeObjectURL: url => revoked.push(url) } });
    await access.authenticate('SYNTHETIC_TEST_CREDENTIAL');
    const first = await access.state(new AbortController().signal);
    assert.equal(first.evidence[0].image_url, 'blob:test-0');
    await access.state(new AbortController().signal);
    assert.equal(calls.filter(call => call.path.endsWith('/image')).length, 1);
    const imageRead = calls.find(call => call.path.endsWith('/image'));
    assert.equal(imageRead.path, '/api/evidence/photo-a/image');
    assert.equal(imageRead.init.headers.get('Authorization'), 'Bearer SYNTHETIC_TEST_CREDENTIAL');
    assert.equal(imageRead.init.cache, 'no-store');
    images = [photo('photo-b')]; await access.state(new AbortController().signal);
    assert.deepEqual(revoked, ['blob:test-0']);
    access.releaseImages(); access.logout(); assert.deepEqual(revoked, ['blob:test-0', 'blob:test-1']);
    assert.equal(JSON.stringify(first).includes('SYNTHETIC_TEST_CREDENTIAL'), false);
  });

  test('image 403 shows unavailable without logout; image 401 clears the entire session', async () => {
    let status = 403;
    const { access } = setup(path => path === '/api/identity' ? response(identity()) : path === '/api/state' ? response(state([photo('photo-a')])) : response({ error: status === 401 ? 'authentication_required' : 'access_denied' }, status));
    await access.authenticate('SYNTHETIC_TEST_CREDENTIAL');
    assert.equal((await access.state(new AbortController().signal)).evidence[0].image_url, null);
    assert.equal(access.snapshot().status, 'ready'); status = 401;
    await assert.rejects(access.state(new AbortController().signal)); assert.equal(access.snapshot().status, 'locked');
  });

  test('logout aborts pending JSON/XHR work, suppresses late progress and never replays writes after re-entry', async () => {
    const pending = deferred(), upload = deferred(), progress = [];
    let uploadArgs;
    const { access, calls } = setup(path => path === '/api/identity' ? response(identity()) : pending.promise, 'release',
      { upload: (...args) => { uploadArgs = args; return upload.promise; } });
    await access.authenticate('SYNTHETIC_TEST_CREDENTIAL');
    const read = access.json('/api/state'); const readCheck = assert.rejects(read);
    const write = access.mutate('/api/tasks/task-a/images', new Blob(['x'], { type: 'image/png' }), key, {}, value => progress.push(value));
    const writeCheck = assert.rejects(write);
    access.logout(); assert.equal(calls.at(-1).init.signal.aborted, true); assert.equal(uploadArgs[3].aborted, true);
    uploadArgs[4](100); assert.deepEqual(progress, []);
    await access.authenticate('SECOND_SYNTHETIC_CREDENTIAL');
    pending.resolve(response(state())); upload.resolve(response({ evidence_id: 'late' }));
    await Promise.all([readCheck, writeCheck]);
    assert.equal(access.snapshot().status, 'ready');
    assert.equal(calls.filter(call => call.init.method === 'POST').length, 0);
    access.logout();
  });

  test('late identity and late image responses cannot cross identities or create unreleased URLs', async () => {
    const oldIdentity = deferred(), oldImage = deferred(); let identities = 0, created = 0;
    const { access } = setup(path => path === '/api/identity' ? (++identities === 1 ? oldIdentity.promise : response(identity('commander', true))) :
      path === '/api/state' ? response(state([photo('photo-a')])) : oldImage.promise,
      'release', { urls: { createObjectURL: () => { created++; return 'blob:late'; }, revokeObjectURL: () => {} } });
    const oldLogin = access.authenticate('FIRST_SYNTHETIC_CREDENTIAL');
    await access.authenticate('SECOND_SYNTHETIC_CREDENTIAL');
    oldIdentity.resolve(response(identity())); assert.equal(await oldLogin, false);
    assert.equal(access.snapshot().identity.role, 'commander');
    const read = access.state(new AbortController().signal); const check = assert.rejects(read);
    await settle(); access.logout(); await access.authenticate('THIRD_SYNTHETIC_CREDENTIAL');
    oldImage.resolve(new Response('late-image')); await check; assert.equal(created, 0); access.logout();
  });

  test('controller clears private state on logout, aborts unmounted work, rejects late responses and stops polling', async () => {
    const pending = deferred(); let reads = 0;
    const { access, calls } = setup(path => path === '/api/identity' ? response(identity()) : (++reads === 1 ? response(state()) : pending.promise));
    await access.authenticate('SYNTHETIC_TEST_CREDENTIAL');
    const controller = new WorkflowController(access, 5); controller.start(); await settle();
    assert.equal(controller.snapshot().state.incident.id, incident);
    controller.refresh(); await settle(); const read = calls.at(-1);
    access.logout(); assert.equal(controller.snapshot().state, null); assert.equal(read.init.signal.aborted, true);
    pending.resolve(response({ ...state(), incident: { id: 'late-private-incident' } })); await settle();
    assert.equal(controller.snapshot().state, null);
    const count = calls.length; await new Promise(resolve => setTimeout(resolve, 20)); assert.equal(calls.length, count);
    assert.equal(await controller.mutate('/api/incidents', {}, 'create'), false);
    controller.stop();
  });

  test('controller unmount during mutation aborts and does not publish success or restore private state', async () => {
    const pending = deferred();
    const { access, calls } = setup((path, init) => path === '/api/identity' ? response(identity()) : init.method === 'POST' ? pending.promise : response(state()));
    await access.authenticate('SYNTHETIC_TEST_CREDENTIAL'); const controller = new WorkflowController(access); controller.start(); await settle();
    const write = controller.mutate('/api/tasks/task-a/reports', { revision: 7, report: 'cannot-access' }, 'report');
    controller.stop(); assert.equal(calls.at(-1).init.signal.aborted, true);
    pending.resolve(response({ evidence_id: 'late' })); assert.equal(await write, false);
    assert.equal(controller.snapshot().state, null); assert.equal(controller.snapshot().busy, false); access.logout();
  });

  test('denied state does not prevent a permitted Commander creation; creation refreshes grants without replay', async () => {
    let created = false, identityReads = 0;
    const { access, calls } = setup((path, init) => {
      if (path === '/api/identity') { identityReads++; return response({ ...identity('commander', true), incident_ids: created ? [incident] : [] }); }
      if (init.method === 'POST') { created = true; return response({ incident_id: incident }); }
      return response({ error: 'access_denied' }, 403);
    });
    await access.authenticate('SYNTHETIC_TEST_CREDENTIAL'); const controller = new WorkflowController(access); controller.start(); await settle();
    assert.equal(controller.snapshot().denied, true); assert.equal(controller.snapshot().state, null);
    const html = renderCommander(null, { release: true, canCreate: true, creationReady: true, disabled: true });
    assert.match(html, /<button class="button primary">Start restriction-to-recovery simulation/);
    assert.equal(await controller.mutate('/api/investigations', {}, 'create'), true);
    assert.equal(identityReads, 2); assert.deepEqual(access.snapshot().identity.incident_ids, [incident]);
    assert.equal(calls.filter(call => call.init.method === 'POST').length, 1); controller.stop(); access.logout();
  });

  test('explicit access refresh revalidates administrator grants and releases cached images', async () => {
    let granted = true; const revoked = [];
    const { access, calls } = setup(path => path === '/api/identity' ? response({ ...identity(), incident_ids: granted ? [incident] : [] }) :
      path === '/api/state' ? response(state([photo('photo-a')])) : new Response('image'), 'release',
      { urls: { createObjectURL: () => 'blob:grant', revokeObjectURL: url => revoked.push(url) } });
    await access.authenticate('SYNTHETIC_TEST_CREDENTIAL'); await access.state(new AbortController().signal);
    granted = false; await access.refreshIdentity();
    assert.deepEqual(access.snapshot().identity.incident_ids, []); assert.deepEqual(revoked, ['blob:grant']);
    assert.equal(calls.at(-1).path, '/api/identity'); assert.equal(calls.at(-1).init.headers.get('Authorization'), 'Bearer SYNTHETIC_TEST_CREDENTIAL'); access.logout();
  });

  test('masked entry, server-role navigation, creation capability and scoped empty histories retain explicit uncertainty', () => {
    const locked = renderLocked(); assert.match(locked, /type="password"/); assert.doesNotMatch(locked, /Investigation workspace|Evidence inspection|Loading server state/);
    const form = renderTokenEntry(); assert.match(form, /<label for="access-token">Access token/); assert.match(form, /autocomplete="off"/i);
    assert.match(form, /Reload requires re-entry/); assert.match(renderTokenEntry(true), /Verifying identity before loading private state/);
    assert.match(renderWrongWorkspace('operator'), /Open Operator workspace/);
    assert.doesNotMatch(renderCommander(state(), { release: true, canCreate: false }), /Start restriction-to-recovery|Start observation-only|Open Operator workspace/);
    const scoped = snapshot(); scoped.planning = []; scoped.events = []; scoped.task = null;
    scoped.journey.maintenance_status = 'not_completed'; scoped.journey.evidence_mode = 'legacy-simulation';
    scoped.journey.approval_current = false; delete scoped.journey.approval_id;
    const html = renderOperator(scoped, { release: true });
    assert.match(html, /No observation task is assigned to your identity/);
    assert.doesNotMatch(html, /Record local pressure report|Record valve position report|Choose next observation|Approve simulated correction|Complete simulated filter replacement|Advance 10 simulated seconds/);
    const assigned = imageTaskState(); assigned.planning = []; assigned.events = [];
    const operator = renderOperator(assigned, { release: true });
    assert.match(operator, /Report cannot access/); assert.match(operator, /Analyze image/);
    assert.doesNotMatch(operator, /Choose next observation|Approve simulated correction|Advance 10 simulated seconds/);
  });

  test('credentials are absent from snapshots, errors, URLs and persisted frontend paths', async () => {
    const secret = 'NONSECRET_SYNTHETIC_SENTINEL';
    const { access, calls } = setup(path => path === '/api/identity' ? response(identity()) : response({ error: secret }, 403));
    await access.authenticate(secret);
    await assert.rejects(access.json('/api/state'), failure => !failure.message.includes(secret) && !failure.code.includes(secret));
    assert.doesNotMatch(JSON.stringify(access.snapshot()), /NONSECRET_SYNTHETIC_SENTINEL/);
    assert.doesNotMatch(JSON.stringify(access), /NONSECRET_SYNTHETIC_SENTINEL/);
    assert.equal(calls.every(call => !call.path.includes(secret)), true);
    for (const file of ['access.ts', 'AccessGate.tsx', 'workflowController.ts', 'useWorkflow.ts', 'identity.ts']) {
      const source = readFileSync(`src/${file}`, 'utf8');
      assert.doesNotMatch(source, /localStorage|sessionStorage|indexedDB|console\.|VITE_.*TOKEN|VITE_.*SECRET/);
    }
    access.logout();
  });

  test('XHR authentication failure clears loaded state and aborts remaining work without a second upload', async () => {
    let uploads = 0;
    const { access } = setup(path => response(path === '/api/identity' ? identity() : state()), 'release', {
      upload: async () => { uploads++; return response({ error: 'authentication_required' }, 401); }
    });
    await access.authenticate('SYNTHETIC_TEST_CREDENTIAL');
    const controller = new WorkflowController(access); controller.start(); await settle();
    assert.equal(controller.snapshot().connection, 'online');
    const ok = await controller.mutate('/api/tasks/task-a/images', new Blob(['x'], { type: 'image/png' }), 'photo', { 'X-Task-Revision': '7', 'X-Evidence-Purpose': 'reference-photo' }, () => {});
    assert.equal(ok, false); assert.equal(uploads, 1); assert.equal(access.snapshot().status, 'locked');
    assert.equal(controller.snapshot().state, null); assert.equal(controller.snapshot().busy, false);
    await access.authenticate('SECOND_SYNTHETIC_CREDENTIAL'); await settle(); assert.equal(uploads, 1);
    controller.stop(); access.logout();
  });

  test('controller unmount releases stored-image URLs exactly once; identity replacement has no cached image reuse', async () => {
    let created = 0; const revoked = [];
    const { access } = setup(path => path === '/api/identity' ? response(identity()) : path === '/api/state' ? response(state([photo('photo-a')])) : new Response('image'),
      'release', { urls: { createObjectURL: () => `blob:unmount-${created++}`, revokeObjectURL: url => revoked.push(url) } });
    await access.authenticate('SYNTHETIC_TEST_CREDENTIAL');
    const controller = new WorkflowController(access); controller.start(); await settle();
    assert.equal(controller.snapshot().state.evidence[0].image_url, 'blob:unmount-0');
    controller.stop(); assert.deepEqual(revoked, ['blob:unmount-0']);
    await access.authenticate('SECOND_SYNTHETIC_CREDENTIAL');
    const next = await access.state(new AbortController().signal);
    assert.equal(next.evidence[0].image_url, 'blob:unmount-1');
    access.logout(); assert.deepEqual(revoked, ['blob:unmount-0', 'blob:unmount-1']);
  });

  test('manual retry retains its UUID within one identity, while reauthentication never replays or reuses the write', async () => {
    const { access, calls } = setup((path, init) => path === '/api/identity' ? response(identity()) : init.method === 'POST' ? response({ error: 'stale_task' }, 409) : response(state()));
    await access.authenticate('SYNTHETIC_TEST_CREDENTIAL');
    const controller = new WorkflowController(access); controller.start(); await settle();
    assert.equal(await controller.mutate('/api/tasks/task-a/reports', { revision: 7, report: 'cannot-access' }, 'report'), false);
    assert.equal(await controller.mutate('/api/tasks/task-a/reports', { revision: 7, report: 'cannot-access' }, 'report'), false);
    const writes = calls.filter(call => call.init.method === 'POST');
    assert.equal(writes.length, 2); assert.equal(writes[0].init.headers.get('Idempotency-Key'), writes[1].init.headers.get('Idempotency-Key'));
    assert.match(writes[0].init.headers.get('Idempotency-Key'), /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/);
    access.logout(); await access.authenticate('SECOND_SYNTHETIC_CREDENTIAL');
    const next = new WorkflowController(access); next.start(); await settle();
    assert.equal(calls.filter(call => call.init.method === 'POST').length, 2);
    await next.mutate('/api/tasks/task-a/reports', { revision: 7, report: 'cannot-access' }, 'report');
    assert.notEqual(calls.filter(call => call.init.method === 'POST')[2].init.headers.get('Idempotency-Key'), writes[0].init.headers.get('Idempotency-Key'));
    next.stop(); controller.stop(); access.logout();
  });

  test('delayed React cleanup of an old controller cannot abort the new identity request or revoke its images', async () => {
    const pending = deferred(); let logins = 0; const revoked = [];
    const { access, calls } = setup(path => path === '/api/identity' ? (++logins === 1 ? response(identity()) : pending.promise) :
      path === '/api/state' ? response(state([photo('photo-a')])) : new Response('image'), 'release',
      { urls: { createObjectURL: () => 'blob:new-owner', revokeObjectURL: url => revoked.push(url) } });
    await access.authenticate('FIRST_SYNTHETIC_CREDENTIAL');
    const old = new WorkflowController(access); old.start(); await settle();
    const login = access.authenticate('SECOND_SYNTHETIC_CREDENTIAL');
    const request = calls.at(-1); old.stop();
    assert.equal(request.path, '/api/identity'); assert.equal(request.init.signal.aborted, false);
    pending.resolve(response(identity('commander', true))); assert.equal(await login, true);
    await access.state(new AbortController().signal); const count = revoked.length;
    old.stop(); assert.equal(revoked.length, count); access.logout();
  });
}
