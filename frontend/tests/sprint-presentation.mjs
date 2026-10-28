// Semantic controls only; these checks do not establish browser layout or clicks.
import { test } from 'node:test';
import assert from 'node:assert/strict';
export function registerSprintPresentation({ renderJourney, snapshot }) {
  test('monitoring is an explicit Commander action after completion, separate from recovery', () => {
    const state=snapshot(); state.journey.recovery.status='observing';
    const commander=renderJourney(state,'commander'),operator=renderJourney(state,'operator');
    assert.match(commander, /<button[^>]*>Start simulated recovery monitoring<\/button>/);
    assert.doesNotMatch(operator, /<button[^>]*>Start simulated recovery monitoring/);
    assert.match(commander, /one 10-second sample per real second/);
    assert.match(commander, /Refresh does not duplicate execution/);
    assert.doesNotMatch(operator, /Approve simulated correction/);
    state.journey.monitoring={status:'running',target_tick:6};
    assert.match(renderJourney(state,'commander'), /<button[^>]*disabled[^>]*>Start simulated recovery monitoring/);
  });
  test('demo time disclosure is explicit while release evidence remains wall-clock based', () => {
    const state=snapshot(); state.journey.time_mode='paused-demo';
    assert.match(renderJourney(state,'commander'), /Simulated human reports age in simulation time/);
    state.journey.time_mode='wall-clock-evidence';
    assert.match(renderJourney(state,'commander'), /Evidence freshness includes wall-clock time/);
    assert.doesNotMatch(renderJourney(state,'commander'), /Walkthrough time pauses/);
  });
  test('verified legacy run has no redundant primary monitoring action', () => {
    assert.doesNotMatch(renderJourney(snapshot(),'commander'), /<button[^>]*>Start simulated recovery monitoring/);
  });
}
