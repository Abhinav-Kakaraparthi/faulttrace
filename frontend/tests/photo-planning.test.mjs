// Static component checks, not a browser, layout, focus or camera acceptance test.
import { test, after } from 'node:test';
import assert from 'node:assert/strict';
import { build } from 'vite';
import { mkdtempSync, writeFileSync, rmSync } from 'node:fs';
import { resolve, join, sep } from 'node:path';
import { pathToFileURL } from 'node:url';

const root = process.cwd();
const temporary = mkdtempSync(resolve('node_modules/.ft011-'));
after(() => {
  if (!temporary.startsWith(join(root, 'node_modules') + sep)) throw new Error('unsafe_cleanup_path');
  rmSync(temporary, { recursive: true, force: true });
});
const output = await build({ configFile: false, logLevel: 'silent',
  build: { ssr: 'tests/presentation-entry.tsx', write: false, rollupOptions: { output: { format: 'es' } } } });
const entry = output.output.find(item => item.type === 'chunk' && item.isEntry);
const file = join(temporary, 'render.mjs');
writeFileSync(file, entry.code);
const { renderCommander, renderOperator, renderEvidenceDetails } = await import(pathToFileURL(file));

function state() {
  const task = { id: 'task-a', revision: 4, asset_id: 'F-17', status: 'awaiting',
    capability: 'READ_LOCAL_DP', creation_source: 'offline provider double', explanation: 'Clarify evidence',
    instruction: 'Observe local differential pressure only.' };
  const photo = { id: 'photo-a', task_id: task.id, asset_id: task.asset_id, kind: 'image', origin: 'user-upload',
    fixture_id: null, sha256: 'test-hash', width: 960, height: 960, report: null,
    status: 'collected', image_url: '/api/evidence/photo-a/image', created_at: '2026-10-26T14:00:00Z',
    submitted_revision: 1, analysis: { id: 'analysis-a', status: 'interpreted', contract: 'photo-observation-v1',
      interpretation: null, receipt: null, accounting: 'recorded', error: null },
    photo_assessment: { evidence_id: 'photo-a', evidence_ref: 'evidence-photo-a', task_id: task.id,
      assigned_asset: task.asset_id, source: 'user-upload', timestamp: '2026-10-26T14:00:00Z',
      status: 'incompatible', identity_status: 'unknown', analysis_status: 'interpreted',
      claim: { category: 'gauge', readability: 'readable', measurement_type: 'pressure', reading: 3.7,
        visible_unit: 'bar', valve_orientation: 'not_applicable', reasons: [] },
      flags: ['identity_unconfirmed', 'pressure_is_not_differential_pressure'], conflicting_refs: [] } };
  return { incident: { id: 'test-incident', revision: 5 }, task, evidence: [photo], planning: [],
    planning_remaining: 4, inference_enabled: false, photo_planning: { version: 1 },
    photo_collection: { version: 1, assets: ['F-17', 'V-08'] }, events: [] };
}

test('both workspaces explain pressure mismatch and preserve photograph inspection', () => {
  const s = state();
  for (const render of [renderCommander, renderOperator]) {
    const html = render(s);
    assert.match(html, /Planning: incompatible/);
    assert.match(html, /Pressure is not differential pressure/);
    assert.match(html, /Why this photo needs follow-up/);
    assert.match(html, /Photographed asset identity remains unconfirmed/);
    assert.match(html, /Original model claim: pressure · 3.7 bar/);
    assert.match(html, /Inspect evidence/);
    assert.match(html, /src="\/api\/evidence\/photo-a\/image"/);
  }
});

test('Operator explicit handoff is available offline but planner and approval remain Commander controls', () => {
  const s = state();
  let html = renderOperator(s);
  assert.match(html, /Send photo for follow-up planning/);
  assert.match(html, /does not accept its reading or complete the measurement task/);
  assert.doesNotMatch(html, /Choose next observation|Approve simulated correction/);
  assert.doesNotMatch(renderCommander(s), /Send photo for follow-up planning/);
  for (const status of ['stale', 'unresolved']) {
    s.evidence[0].photo_assessment.status = status;
    s.evidence[0].photo_assessment.claim = null;
    html = renderOperator(s);
    assert.doesNotMatch(html, /Send photo for follow-up planning/);
  }
});

test('accepted photo citation is inspectable by Commander and clarification task links its source in Operator', () => {
  const s = state();
  s.task = { ...s.task, id: 'task-follow-up', asset_id: 'V-08', source_photo_ids: ['photo-a'] };
  s.planning = [{ id: 'plan-a', status: 'accepted', context_revision: 5, task_id: s.task.id,
    proposal: { kind: 'REQUEST_OBSERVATION', asset_id: 'V-08', capability: 'OBSERVE_POSITION',
      evidence_refs: ['evidence-photo-a'], explanation_code: 'clarify_conflict' } }];
  const commander = renderCommander(s);
  assert.match(commander, /Latest accepted proposal cites/);
  assert.match(commander, /Inspect cited photograph · assigned F-17/);
  const operator = renderOperator(s);
  assert.match(operator, /Clarify photographic evidence/);
  assert.match(operator, /Inspect source photograph · assigned F-17/);
  assert.doesNotMatch(operator, /Choose next observation/);
});

test('full inspection explains disputed, unreadable and stale model claims without dropping original record', () => {
  const s = state();
  for (const flag of ['human_model_numeric_disagreement', 'human_model_readability_disagreement', 'stale_or_superseded', 'reading_not_established']) {
    s.evidence[0].photo_assessment.flags = [flag];
    const html = renderEvidenceDetails(s.evidence[0]);
    assert.match(html, /Full image · no crop/);
    assert.match(html, /<details open=""><summary>Why this photo needs follow-up/);
    assert.match(html, /No photo claim satisfies the correction checklist/);
    assert.doesNotMatch(html, /Further review is required/);
  }
});

test('historical backend without photo bridge remains compatible and makes no handoff claim', () => {
  const s = state();
  delete s.photo_planning;
  delete s.evidence[0].photo_assessment;
  assert.doesNotMatch(renderOperator(s), /Send photo for follow-up planning/);
  assert.doesNotMatch(renderCommander(s), /Planning: incompatible/);
});
