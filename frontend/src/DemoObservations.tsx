import type { WorkspaceProps } from './workspace';
const labels: Record<string, string> = {
  'OBSERVE_F-17_READ_LOCAL_DP': 'Assign F-17 observation',
  'OBSERVE_V-08_OBSERVE_POSITION': 'Assign V-08 observation',
  ESCALATE_HUMAN_INVESTIGATION: 'Escalate for human investigation',
};
export function DemoObservations({ state, mutate, disabled }: WorkspaceProps) {
  if (!state?.demo || state.demo.live || !state.incident) return null;
  const blocked = !!state.task && ['awaiting','submitted','analyzing'].includes(state.task.status);
  return <details className="section-surface model-workflow"><summary>Demo observation templates — no AI inference</summary>
    <p>Application-assigned observations, not NVIDIA choices. Reports and correction still pass the same evidence policy. {state.demo.assignment_remaining} template assignments remain.</p>
    {blocked && <p>Complete or refuse the active task before assigning another.</p>}
    <div className="server-evidence-actions">{state.demo.template_actions.filter(action => labels[action]).map(action =>
      <button className="button secondary" key={action} disabled={disabled || blocked || !state.demo!.assignment_remaining}
        onClick={() => void mutate('/api/demo/observations', { action_id: action, revision: state.incident!.revision }, `demo-${action}-${state.incident!.revision}`)}>{labels[action]}</button>)}</div>
  </details>;
}
