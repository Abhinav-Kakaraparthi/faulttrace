import { test } from 'node:test';
import assert from 'node:assert/strict';
import { initial, reduceDemo } from '../src/demo.ts';
import { planningBlocker } from '../src/planningPolicy.ts';
import { httpDiagnosticSummary } from '../src/api.ts';

test('HTTP diagnostics display safe status categories and retain historical unknowns', () => {
  assert.equal(httpDiagnosticSummary({ error: 'provider_network_error' }), null);
  assert.match(httpDiagnosticSummary({ error: 'provider_http_error' }), /HTTP status: unknown.*Category: unknown/);
  assert.match(httpDiagnosticSummary({ error: 'provider_http_error', http_status: null, http_error_category: null }), /HTTP status: unknown.*Category: unknown/);
  assert.match(httpDiagnosticSummary({ error: 'provider_http_error', http_status: 401, http_error_category: 'http_unauthorized' }), /HTTP status: 401.*Category: http_unauthorized.*cause is not established/);
});

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

test('a rejected attempted context stays blocked with three turns remaining; a different revision alone cannot override a blocking task', () => {
  const attempted = { ...planningReady, incident: { revision: 1 }, planning_remaining: 3,
    planning: [{ status: 'rejected', context_revision: 1 }] };
  assert.match(planningBlocker(attempted), /already has an attempt/);
  assert.match(planningBlocker({ ...attempted, incident: { revision: 2 }, task: { status: 'awaiting' } }), /Finish or report/);
  assert.equal(planningBlocker({ ...attempted, incident: { revision: 3 }, task: { status: 'needs_evidence' } }), null);
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


// Policy examples use independently stated expected outcomes; no provider or backend.
const { canApprove, canExecute, recoveryLabel } = await import('../src/journeyState.ts');
const readyJourney = { maintenance_status: 'not_completed', approval_current: false,
  assessment: { eligible: true }, recovery: { status: 'not_started' } };
test('simulated correction requires explicit consent for the exact displayed revision', () => {
  assert.equal(canApprove(readyJourney, 7, null), false);
  assert.equal(canApprove(readyJourney, 7, 6), false);
  assert.equal(canApprove(readyJourney, 7, 7), true);
  assert.equal(canApprove({ ...readyJourney, assessment: { eligible: false } }, 7, 7), false);
  assert.equal(canApprove({ ...readyJourney, approval_current: true }, 7, 7), false);
  assert.equal(canApprove({ ...readyJourney, maintenance_status: 'simulated_replacement_completed' }, 7, 7), false);
});
test('operator execution requires current approval and corroborated evidence; completion cannot imply recovery', () => {
  assert.equal(canExecute(readyJourney), false);
  assert.equal(canExecute({ ...readyJourney, approval_current: true }), true);
  assert.equal(canExecute({ ...readyJourney, approval_current: true, assessment: { eligible: false } }), false);
  assert.equal(canExecute({ ...readyJourney, approval_current: true, maintenance_status: 'simulated_replacement_completed' }), false);
  assert.equal(recoveryLabel('observing'), 'Observing post-correction samples');
  assert.equal(recoveryLabel('failed'), 'Recovery verification failed');
  assert.equal(recoveryLabel('verified'), 'Simulated operating recovery verified');
});


const { resolveRoute } = await import('../src/routing.ts');
test('dedicated routes override obsolete query controls; legacy connected URLs keep unrelated query and fragment', () => {
  for (const [path, workspace, canonical] of [
    ['/commander', 'commander', '/commander'], ['/operator', 'operator', '/operator'],
    ['/?mode=connected&view=operator', 'operator', '/operator'],
    ['/?mode=connected', 'commander', '/commander'],
    ['/?view=operator&source=bookmark#task', 'operator', '/operator?source=bookmark#task'],
    ['/operator/?mode=sample&view=commander', 'operator', '/operator'],
    ['/commander?view=operator', 'commander', '/commander'],
  ]) {
    assert.deepEqual(resolveRoute(new URL(path, 'http://localhost:5180')), {kind: 'connected', workspace, canonical});
  }
  assert.equal(resolveRoute(new URL('http://localhost:5180/?mode=sample')).kind, 'sample');
  assert.equal(resolveRoute(new URL('http://localhost:5180/missing')).kind, 'not-found');
});
