import { test } from 'node:test';
import assert from 'node:assert/strict';
import { initial, reduceDemo } from '../src/demo.ts';
import { planningBlocker } from '../src/planningPolicy.ts';

const planningReady = { task: null, planning: [], incident: { revision: 2 }, planning_remaining: 4, inference_enabled: true };
test('connected planner is available only after explicit incident creation and no blocking task', () => {
  assert.equal(planningBlocker(planningReady), null);
  for (const status of ['awaiting', 'submitted', 'analyzing']) {
    assert.match(planningBlocker({ ...planningReady, task: { status } }), /Finish or report/);
  }
  for (const status of ['observed', 'needs_evidence']) {
    assert.equal(planningBlocker({ ...planningReady, task: { status } }), null);
  }
});
test('disabled inference, pending reservation, spent budget and duplicate context explain disabled actions', () => {
  assert.match(planningBlocker({ ...planningReady, inference_enabled: false }), /Inference disabled/);
  assert.match(planningBlocker({ ...planningReady, planning: [{ status: 'pending', context_revision: 1 }] }), /pending/);
  assert.match(planningBlocker({ ...planningReady, planning_remaining: 0 }), /Budget exhausted/);
  assert.match(planningBlocker({ ...planningReady, planning: [{ status: 'rejected', context_revision: 2 }] }), /already has an attempt/);
});

test('incident starts with an observation request and no completed evidence', () => {
  const state = reduceDemo(initial, { type: 'start' });
  assert.equal(state.started, true);
  assert.equal(state.waiting, true);
  assert.equal(state.evidence.length, 0);
  assert.deepEqual(state.activity.map(event => event.title), ['Sample incident started', 'Local observation requested']);
  assert.deepEqual(initial.activity, []);
});

for (const outcome of ['readable', 'unreadable', 'cannot-access', 'wrong-equipment']) {
  test(`${outcome} records a distinct observation, never a recovery`, () => {
    const start = reduceDemo(initial, { type: 'start' });
    const state = reduceDemo(start, { type: 'submit', outcome, fixture: outcome === 'readable' ? 'a' : undefined, note: ' field context ' });
    assert.equal(state.waiting, false);
    assert.equal(state.started, true);
    assert.equal(state.evidence[0].outcome, outcome);
    assert.equal(state.evidence[0].note, 'field context');
    assert.equal(state.activity.at(-1).evidence, 1);
    const message = state.activity.at(-1).detail;
    if (outcome === 'readable') assert.match(message, /180 kPa.*not a diagnosis/);
    if (outcome === 'unreadable') assert.match(message, /No numeric reading recorded/);
    if (outcome === 'cannot-access') assert.match(message, /No equipment observation/);
    if (outcome === 'wrong-equipment') assert.match(message, /Asset identity disputed/);
    assert.equal('recovery' in state, false);
    assert.equal(reduceDemo(state, { type: 'submit', outcome: 'readable', note: '' }), state);
  });
}

test('reset removes the sample journey; repeat observation preserves earlier evidence', () => {
  const observed = reduceDemo(reduceDemo(initial, { type: 'start' }), { type: 'submit', outcome: 'unreadable', fixture: 'b', note: '' });
  const reopened = reduceDemo(observed, { type: 'reopen' });
  assert.equal(reopened.waiting, true);
  assert.equal(reopened.evidence[0].outcome, 'unreadable');
  const second = reduceDemo(reopened, { type: 'submit', outcome: 'readable', fixture: 'a', note: '' });
  assert.deepEqual(second.evidence.map(item => item.id), [1, 2]);
  assert.equal(second.activity.length, 5);
  assert.deepEqual(reduceDemo(second, { type: 'reset' }), initial);
  assert.equal(reduceDemo(initial, { type: 'submit', outcome: 'readable', note: '' }), initial);
});
