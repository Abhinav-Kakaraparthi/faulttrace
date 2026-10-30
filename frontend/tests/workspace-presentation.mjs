// Deterministic server-state/presentation checks; no browser or provider calls.
import { test } from 'node:test';
import assert from 'node:assert/strict';

export function registerWorkspacePresentation({ investigationStage, renderCommander, renderOperator, renderSignals, snapshot, imageTaskState }) {
  function ready() {
    const state = snapshot();
    Object.assign(state, { task: null, tasks: [], evidence: [], planning: [], planning_remaining: 4, inference_enabled: true });
    Object.assign(state.journey, { maintenance_status: 'not_completed', approval_current: false, approval_id: null, monitoring: null });
    state.journey.recovery = { status: 'not_started', sample_count: 0, window_seconds: 0, sample_refs: [] };
    state.journey.assessment.eligible = false;
    return state;
  }
  const attempt = (state, status) => ({ id: 'attempt-state', context_revision: state.incident.revision, status, proposal: null, receipt: null });

  test('awaiting planning leads with the actual next control before process and real telemetry', () => {
    const state = ready(), before = JSON.stringify(state), html = renderCommander(state);
    assert.equal(investigationStage(state, 'commander').key, 'awaiting_planning');
    assert.ok(html.indexOf('Awaiting the next observation') < html.indexOf('Choose next observation'));
    assert.ok(html.indexOf('Choose next observation') < html.indexOf('Process overview'));
    assert.ok(html.indexOf('Process overview') < html.indexOf('Stored simulated telemetry'));
    assert.match(html, /Scrollable P-04 F-17 V-08 process schematic/);
    assert.match(html, /Deterministic assessment and correction conditions/);
    assert.doesNotMatch(html, /vibration|collaborative memory|AI diagnosis complete|continuous telemetry/i);
    assert.equal(JSON.stringify(state), before);
  });
  test('planning has no invented completion percentage or ready observation', () => {
    const state = ready(); state.planning = [attempt(state, 'pending')];
    const stage = investigationStage(state, 'commander'), html = renderCommander(state);
    assert.equal(stage.key, 'planning');
    assert.match(stage.title, /in progress/);
    assert.match(html, /<button[^>]*disabled[^>]*>Planning request pending/);
    assert.doesNotMatch(html, /Open operator task|<progress/);
  });
  test('assigned equipment, instructions and photo inputs lead the Operator evidence history', () => {
    const state = imageTaskState(), before = JSON.stringify(state);
    state.evidence = [];
    assert.equal(investigationStage(state, 'operator').key, 'observation');
    const html = renderOperator(state);
    assert.ok(html.indexOf('F-17') < html.indexOf('Take a photograph'));
    assert.ok(html.indexOf(state.task.instruction) < html.indexOf('Take a photograph'));
    assert.ok(html.indexOf('Take a photograph') < html.indexOf('Investigation evidence'));
    assert.match(html, /Report cannot access|Report cannot-access|Report cannot access/i);
    assert.doesNotMatch(html, /Choose next observation|Approve simulated correction/);
    assert.equal(JSON.stringify(state), JSON.stringify({ ...JSON.parse(before), evidence: [] }));
  });
  test('collected or analyzing evidence is review, never a verified measurement or recovery', () => {
    const state = imageTaskState(); state.evidence[0].status = 'collected';
    assert.equal(investigationStage(state, 'commander').key, 'evidence_review');
    state.evidence[0].analysis = { id: 'pending-analysis', status: 'pending' };
    assert.equal(investigationStage(state, 'operator').title, 'Evidence analysis in progress');
    assert.doesNotMatch(investigationStage(state, 'commander').next, /measurement verified|recovery verified/i);
  });
  test('human escalation supersedes an inactive prior assignment and retains history', () => {
    const state = ready(); state.task = { ...imageTaskState().task, status: 'refused' };
    state.planning = [attempt(state, 'escalated')];
    assert.equal(investigationStage(state, 'operator').key, 'human_escalation');
    const html = renderOperator(state);
    assert.match(html, /No new Operator observation is assigned/);
    assert.match(html, /<summary>Previous observation assignment/);
    assert.ok(html.indexOf('Human investigation requested') < html.indexOf('Previous observation assignment'));
  });
  test('approval and independent recovery stages come only from their stored state', () => {
    const state = ready(); state.journey.assessment.eligible = true;
    assert.equal(investigationStage(state, 'commander').key, 'approval');
    assert.match(investigationStage(state, 'commander').title, /approval review/);
    state.journey.approval_current = true; state.journey.approval_id = 'approval-current';
    assert.equal(investigationStage(state, 'operator').title, 'Simulated correction approved');
    state.journey.maintenance_status = 'simulated_replacement_completed';
    assert.equal(investigationStage(state, 'commander').key, 'recovery_verification');
    assert.doesNotMatch(investigationStage(state, 'commander').title, /verified/);
    state.journey.recovery.status = 'observing';
    assert.match(investigationStage(state, 'commander').title, /Observing/);
    state.journey.recovery.status = 'failed';
    assert.match(investigationStage(state, 'commander').title, /failed/);
    state.journey.recovery.status = 'verified';
    assert.match(investigationStage(state, 'commander').title, /recovery verified/);
  });
  test('compact telemetry preserves zero, units and stored-time scope without sample substitution', () => {
    const sample = { ...snapshot().journey.samples[0], flow: 0, pressure: 0, valve: 0, alarm: null };
    const html = renderSignals([sample]);
    assert.match(html, /<strong>0 <small>m3\/h/);
    assert.match(html, /<strong>0 <small>kPa/);
    assert.match(html, /Stored sample history \(1\).*stepped simulation/);
    assert.match(html, /Simulated measurement time \(UTC\)/);
    assert.match(renderSignals([]), /No timestamped simulator measurements/);
    assert.doesNotMatch(renderSignals([]), /184|182|85 m3/);
  });
}
