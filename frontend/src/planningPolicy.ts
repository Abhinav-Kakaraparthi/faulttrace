import type { ServerState } from './api';

export function escalatedWithoutTask(state: Pick<ServerState, 'task' | 'planning' | 'incident'>): boolean {
  const latest = state.planning.at(-1);
  return !state.task && latest?.status === 'escalated' && latest.context_revision === state.incident?.revision;
}

/** Presentation guard only; the backend independently enforces all policy. */
export function planningBlocker(state: Pick<ServerState, 'task' | 'planning' | 'incident' | 'planning_remaining' | 'inference_enabled'>): string | null {
  if (!state.inference_enabled) return 'Inference disabled. See the startup guide; no model choice is substituted.';
  if (state.planning.some(item => item.status === 'pending')) return 'Planning is pending. No additional call will be made.';
  if (escalatedWithoutTask(state)) return 'Human review requested. No Operator task was created. Review the cited evidence and planning history; this context will not be retried.';
  if (state.task && ['awaiting', 'submitted', 'analyzing'].includes(state.task.status)) return 'Finish or report the current task first. A photo needs explicit analysis and follow-up handoff, or a human report.';
  if (!state.planning_remaining) return 'Budget exhausted. Human investigation is required.';
  if (state.planning.some(item => item.context_revision === state.incident?.revision)) return 'This context already has an attempt. It will not be retried; new evidence is required.';
  return null;
}
