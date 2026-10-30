// Static semantics only; not a browser or layout acceptance test.
import { test } from 'node:test';
import assert from 'node:assert/strict';

export function registerEscalationPresentation({ renderPlanner, renderOperator, imageTaskState }) {
  test('human escalation is an honest no-task state in both workspaces, with citations and history', () => {
    const state = { ...imageTaskState(), task: null, tasks: [], planning_remaining: 3,
      incident: { id: 'incident-reviewed', revision: 1 }, inference_enabled: true,
      planning: [{ id: 'attempt-reviewed', status: 'escalated', context_revision: 1,
        proposal: { kind: 'ESCALATE', asset_id: 'HUMAN', capability: 'HUMAN_INVESTIGATION',
          context_revision: 1, evidence_refs: ['sample-reviewed'], explanation_code: 'human_review' },
        explanation: 'Application-generated summary', task_id: null, receipt: null }] };
    const commander = renderPlanner(state), operator = renderOperator(state);
    assert.match(commander, /Human investigation requested/);
    assert.match(commander, /no Operator observation task was created/);
    assert.match(commander, /not a diagnosis or proof that every observation was tried/);
    assert.match(commander, /sample-reviewed/);
    assert.match(commander, /Planning history/);
    assert.doesNotMatch(commander, /<button[^>]*>Choose next observation<\/button>/);
    assert.doesNotMatch(commander, /Open operator task/);
    assert.match(operator, /No Operator observation is assigned: this incident was escalated/);
    assert.doesNotMatch(operator, /Waiting for Commander to assign an observation/);
  });
}
