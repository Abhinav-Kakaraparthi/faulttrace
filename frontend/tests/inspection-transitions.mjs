// Real workflow transitions + actual Connected rendering with an injected hook
// snapshot. The native-dialog adapter is exercised with a deterministic double.
// This is offline rendering/lifecycle coverage, not browser verification.
import { test, after } from 'node:test';
import assert from 'node:assert/strict';
import { build } from 'vite';
import { mkdtempSync, writeFileSync, rmSync } from 'node:fs';
import { resolve, join, sep } from 'node:path';
import { pathToFileURL } from 'node:url';

export async function registerInspectionTests() {
  const root = process.cwd();
  const temporary = mkdtempSync(resolve('node_modules/.inspection-transitions-'));
  after(() => {
    delete globalThis.__inspectionServer;
    if (!temporary.startsWith(join(root, 'node_modules') + sep)) throw new Error('unsafe_cleanup_path');
    rmSync(temporary, { recursive: true, force: true });
  });
  const output = await build({ configFile: false, logLevel: 'silent',
    plugins: [{ name: 'inspection-server-snapshot', enforce: 'pre', transform(_source, id) {
      if (id.replaceAll('\\', '/').endsWith('/src/useWorkflow.ts')) return 'export function useWorkflow() { return globalThis.__inspectionServer; }';
    } }],
    build: { ssr: 'tests/presentation-entry.tsx', write: false, rollupOptions: { output: { format: 'es' } } } });
  const file = join(temporary, 'render.mjs');
  writeFileSync(file, output.output.find(item => item.type === 'chunk' && item.isEntry).code);
  const { AccessSession, WorkflowController, renderConnected, synchronizeInspectionDialog } = await import(pathToFileURL(file));
  const incident = '11111111-2222-4333-8444-555555555555';
  const identity = { profile: 'release', principal_id: 'operator-review', role: 'operator', capabilities: { create_incident: false }, incident_ids: [incident] };
  const selectedId = '7d510cbb-9577-4be8-8f03-d1816e2cd231';
  const otherId = 'aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee';
  const record = (id = selectedId) => ({ id, task_id: 'task-a', kind: 'image', origin: 'private-provenance-original', fixture_id: null,
    asset_id: 'F-17', report: null, created_at: '2026-10-27T12:00:00Z', status: 'collected', submitted_revision: 1, image_url: '/ignored',
    width: 480, height: 300, sha256: 'private-sha-original', analysis: { id: 'analysis-a', status: 'interpreted', accounting: 'recorded', error: null, receipt: null,
      interpretation: { readability: 'readable', reading: 417, unit: 'kPa', evidence_ref: 'private-interpretation-original' } } });
  const state = evidence => ({ incident: { id: incident, revision: 7 }, task: null, evidence, planning: [], events: [], planning_remaining: 4, inference_enabled: false });
  const response = (value, status = 200) => new Response(JSON.stringify(value), { status });
  const settle = async () => { for (let i = 0; i < 12; i++) await new Promise(resolve => setImmediate(resolve)); };
  const deferred = () => { let resolve; const promise = new Promise(done => { resolve = done; }); return { promise, resolve }; };

  async function setup(selected = record()) {
    let reply = () => response(state([selected, record(otherId)]));
    let write = () => response({ error: 'inference_disabled' }, 403);
    const revoked = []; const requests = [];
    const access = new AccessSession('release', { fetch: async (path, init) => {
      requests.push({ path, init });
      if (path === '/api/identity') return response(identity);
      if (path.endsWith('/image')) return new Response('synthetic-image', { headers: { 'Content-Type': 'image/png' } });
      return init.method === 'POST' ? write() : reply();
    }, urls: { createObjectURL: () => `blob:private-${requests.length}`, revokeObjectURL: url => revoked.push(url) } });
    await access.authenticate('OFFLINE_SYNTHETIC_CREDENTIAL');
    const controller = new WorkflowController(access);
    const dialog = { open: false, opens: 0, closes: 0, showModal() { this.open = true; this.opens++; }, close() { this.open = false; this.closes++; } };
    const frame = () => {
      const snapshot = controller.snapshot();
      globalThis.__inspectionServer = { ...snapshot, inspect: controller.inspect, refresh: controller.refresh, mutate: controller.mutate };
      const html = renderConnected();
      synchronizeInspectionDialog(dialog, !!snapshot.inspectionId);
      return { html, details: html.match(/<div class="dialog-content">([\s\S]*?)<\/dialog>/)?.[1] ?? '' };
    };
    const unsubscribe = controller.subscribe(frame); controller.start(); await settle();
    return { access, controller, dialog, frame, revoked, requests,
      reply: next => { reply = next; }, write: next => { write = next; },
      stop: () => { unsubscribe(); controller.stop(); access.logout(); } };
  }

  const assertEmpty = view => {
    for (const marker of [selectedId, 'private-provenance-original', 'private-sha-original', 'private-interpretation-original', 'blob:private-', '417']) assert.equal(view.details.includes(marker), false, marker);
    assert.doesNotMatch(view.details, /<img|Evidence ID|NVIDIA interpretation/);
  };

  test('open then state denial removes details immediately, closes dialog, clears selection and revokes images', async () => {
    for (const selected of [record(), { ...record(), kind: 'report', analysis: null, image_url: null, report: 'private-report-original' }]) {
    const run = await setup(selected);
    try {
      run.controller.inspect(selectedId); const before = run.frame();
      const markers = selected.kind === 'image' ? [selectedId, 'private-provenance-original', '417', 'blob:private-'] : [selectedId, 'private-provenance-original', 'private-report-original'];
      for (const marker of markers) assert.ok(before.details.includes(marker), marker);
      assert.equal(run.dialog.open, true);
      run.reply(() => response({ error: 'access_denied' }, 403)); run.controller.refresh(); await settle();
      assert.equal(run.access.snapshot().status, 'ready'); assert.equal(run.controller.snapshot().denied, true);
      assert.equal(run.controller.snapshot().state, null); assert.equal(run.controller.snapshot().inspectionId, null);
      const after = run.frame(); assertEmpty(after); assert.doesNotMatch(after.html, new RegExp(selectedId));
      assert.match(after.html, /Incident access denied/); assert.equal(run.dialog.open, false); assert.equal(run.dialog.closes, 1);
      assert.equal(run.revoked.length, selected.kind === 'image' ? 2 : 1);
      run.reply(() => response(state([selected, record(otherId)]))); run.controller.refresh(); await settle();
      assertEmpty(run.frame()); assert.equal(run.dialog.open, false); assert.equal(run.controller.snapshot().inspectionId, null);
      run.controller.inspect(selectedId); assert.match(run.frame().details, new RegExp(selectedId)); assert.equal(run.dialog.open, true);
    } finally { run.stop(); }
    }
  });

  test('removing selected evidence closes inspection, retains unrelated authorized evidence and does not restore selection on reintroduction', async () => {
    const run = await setup();
    try {
      run.controller.inspect(selectedId); assert.equal(run.dialog.open, true);
      run.reply(() => response(state([record(otherId)]))); run.controller.refresh(); await settle();
      assertEmpty(run.frame()); assert.equal(run.dialog.open, false); assert.equal(run.controller.snapshot().inspectionId, null);
      assert.equal(run.controller.snapshot().state.evidence.length, 1); assert.match(run.frame().html, new RegExp(otherId));
      run.reply(() => response(state([record(), record(otherId)]))); run.controller.refresh(); await settle();
      assertEmpty(run.frame()); assert.equal(run.dialog.open, false);
      run.controller.inspect(otherId); assert.match(run.frame().details, new RegExp(otherId)); assert.doesNotMatch(run.frame().details, new RegExp(selectedId));
    } finally { run.stop(); }
  });

  test('authorized record refresh uses current details without reopening or retaining old provenance/interpretation', async () => {
    const run = await setup();
    try {
      run.controller.inspect(selectedId);
      const next = { ...record(), origin: 'authorized-refreshed-origin', sha256: 'authorized-refreshed-sha', analysis: {
        ...record().analysis, interpretation: { readability: 'readable', reading: 23, unit: 'kPa', evidence_ref: 'refreshed-reference' } } };
      run.reply(() => response(state([next, record(otherId)]))); run.controller.refresh(); await settle();
      const current = run.frame(); assert.match(current.details, /authorized-refreshed-origin|authorized-refreshed-sha/);
      assert.match(current.details, /23 kPa/); assert.doesNotMatch(current.details, /private-provenance-original|private-sha-original|417 kPa/);
      assert.equal(run.dialog.open, true); assert.equal(run.dialog.opens, 1); assert.equal(run.dialog.closes, 0);
    } finally { run.stop(); }
  });

  test('application inference-disabled 403 preserves identity and authorized inspection; access-denied mutation clears inspection', async () => {
    const run = await setup();
    try {
      run.controller.inspect(selectedId);
      assert.equal(await run.controller.mutate('/api/evidence/photo-a/analyze', { revision: 7 }, 'analyze'), false);
      assert.equal(run.access.snapshot().status, 'ready'); assert.equal(run.controller.snapshot().inspectionId, selectedId);
      assert.equal(run.dialog.open, true); assert.match(run.frame().details, new RegExp(selectedId));
      run.write(() => response({ error: 'access_denied' }, 403));
      await run.controller.mutate('/api/evidence/photo-a/analyze', { revision: 7 }, 'analyze');
      assert.equal(run.access.snapshot().status, 'ready'); assert.equal(run.controller.snapshot().inspectionId, null);
      assertEmpty(run.frame()); assert.equal(run.dialog.open, false);
    } finally { run.stop(); }
  });

  test('logout or identity replacement clears inspection and late responses cannot restore details', async () => {
    for (const change of ['logout', 'identity']) {
      const run = await setup(); const pending = deferred();
      try {
        run.controller.inspect(selectedId); run.reply(() => pending.promise); run.controller.refresh(); await settle();
        if (change === 'logout') run.access.logout(); else await run.access.authenticate('SECOND_OFFLINE_SYNTHETIC_CREDENTIAL');
        assert.equal(run.controller.snapshot().inspectionId, null); assert.equal(run.controller.snapshot().state, null);
        assertEmpty(run.frame()); assert.equal(run.dialog.open, false);
        pending.resolve(response(state([record()]))); await settle();
        assertEmpty(run.frame()); assert.equal(run.controller.snapshot().inspectionId, null);
      } finally { pending.resolve(response(state([]))); run.stop(); }
    }
  });

  test('explicit state clear on unmount and authentication-required 401 close and never restore inspection', async () => {
    for (const change of ['stop', '401']) {
      const run = await setup();
      try {
        run.controller.inspect(selectedId);
        if (change === 'stop') run.controller.stop();
        else { run.reply(() => response({ error: 'authentication_required' }, 401)); run.controller.refresh(); await settle(); }
        assertEmpty(run.frame()); assert.equal(run.controller.snapshot().inspectionId, null); assert.equal(run.dialog.open, false);
        assert.equal(run.access.snapshot().status, change === '401' ? 'locked' : 'ready');
        run.controller.inspect(selectedId); assertEmpty(run.frame());
      } finally { run.stop(); }
    }
  });
}
