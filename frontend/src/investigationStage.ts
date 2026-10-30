import type { ServerState } from './api';
import { nextJourneyAction } from './JourneyOutcome';
import { recoveryLabel } from './journeyState';

export type InvestigationStage = {
  key: 'awaiting_planning' | 'planning' | 'observation' | 'evidence_review' | 'human_escalation' | 'approval' | 'recovery_verification';
  title: string; next: string; tone: 'neutral' | 'active' | 'attention' | 'complete';
};

/** Read-only presentation of stored state. Never authorizes or advances workflow. */
export function investigationStage(state: ServerState, view: 'commander' | 'operator'): InvestigationStage {
  const j = state.journey, task = state.task;
  if (j && (j.maintenance_status !== 'not_completed' || ['verified', 'failed'].includes(j.recovery.status))) {
    return { key: 'recovery_verification', title: recoveryLabel(j.recovery.status),
      next: nextJourneyAction(j, view), tone: j.recovery.status === 'verified' ? 'complete' : j.recovery.status === 'failed' ? 'attention' : 'active' };
  }
  if (j?.approval_current && j.approval_id) return { key: 'approval', title: 'Simulated correction approved',
    next: nextJourneyAction(j, view), tone: 'active' };
  if (state.planning.some(item => item.status === 'pending')) return { key: 'planning', title: 'Planning request in progress',
    next: 'A planning request is in progress. Its validated result will appear here.', tone: 'active' };
  if (task?.status === 'analyzing' || state.evidence.some(item => item.analysis?.status === 'pending')) {
    return { key: 'evidence_review', title: 'Evidence analysis in progress',
      next: 'Wait for the recorded interpretation. Model claims and independent human observations remain separate.', tone: 'active' };
  }
  const latest = state.planning.at(-1);
  const blocking = task && ['awaiting', 'submitted', 'analyzing'].includes(task.status);
  if (!blocking && latest?.status === 'escalated' && latest.context_revision === state.incident?.revision) {
    return { key: 'human_escalation', title: 'Human investigation requested', tone: 'attention',
      next: view === 'commander' ? 'Review the cited evidence and decision history. Escalation does not create an Operator observation or establish a diagnosis.'
        : 'No new Operator observation is assigned. Commander can review the escalation and cited evidence; no equipment action is authorized.' };
  }
  if (j?.assessment.eligible) return { key: 'approval', title: 'Evidence ready for approval review',
    next: nextJourneyAction(j, view), tone: 'attention' };
  if (task && (['submitted', 'observed'].includes(task.status) || state.evidence.some(item => item.task_id === task.id))) {
    return { key: 'evidence_review', title: 'Review submitted evidence', tone: 'attention',
      next: view === 'commander' ? 'Inspect readability, provenance and independent reports. Resolve gaps before approval or another planning request.'
        : 'Review your submitted image and provide an independent report, clarification or refusal. Answers are never copied from the model.' };
  }
  if (task && ['awaiting', 'needs_evidence'].includes(task.status)) return { key: 'observation',
    title: `${task.asset_id} observation assigned`, tone: 'active', next: view === 'commander'
      ? 'Operator can collect the assigned observation. Review its evidence before choosing another task.'
      : 'Collect the assigned evidence below, or report why it cannot be provided.' };
  if (latest && latest.context_revision === state.incident?.revision && latest.status !== 'accepted') {
    return { key: 'evidence_review', title: 'Planning result needs review',
      next: 'Review the saved result and diagnostics. The same context is not automatically retried.', tone: 'attention' };
  }
  return { key: 'awaiting_planning', title: 'Awaiting the next observation', tone: 'neutral',
    next: view === 'operator' ? 'No observation is assigned yet. Commander chooses the next permitted step.'
      : state.inference_enabled ? 'Choose an informative observation or human review. A validated proposal can create the Operator task.'
        : 'Inference is disabled. Explicit offline templates, when available, remain labeled application assignments.' };
}
