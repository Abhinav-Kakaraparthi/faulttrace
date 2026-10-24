import { type Demo, outcomeLabels } from './demo';
import { Icon } from './Icon';

export function ObservationTask({ demo, goOperator, reopen }: {
  demo: Demo; goOperator: () => void; reopen: () => void;
}) {
  const latest = demo.evidence.at(-1);
  const state = !demo.started ? 'Not assigned' : demo.waiting ? 'Awaiting observation'
    : latest ? outcomeLabels[latest.outcome] : 'Investigation open';
  return <section className="observation-task section-surface" aria-labelledby="observation-task-title">
    <div className="observation-task-heading">
      <span className="eyebrow">{demo.started ? 'ACTIVE OBSERVATION TASK' : 'PLANNED OBSERVATION TASK'}</span>
      <span className={`pill ${!demo.started ? 'neutral' : latest?.outcome === 'readable' && !demo.waiting ? 'teal' : 'amber'}`}>{state}</span>
    </div>
    <div className="observation-equipment"><span className="equipment-tag">F-17</span><div>
      <span className="quiet-label">{demo.started ? 'Assigned equipment' : 'Planned equipment'}</span>
      <h2 id="observation-task-title">Return-line filter</h2>
    </div></div>
    <h3>Read the local DP indicator.</h3>
    <p className="requested-evidence">Capture the differential-pressure display and unit. If unavailable, report unreadable, blocked access, or wrong equipment.</p>
    <details className="inline-rationale"><summary>Why this task?</summary><p>Compare a local pressure observation with telemetry before choosing between restriction, sensor discrepancy, and valve mismatch. The task provides evidence, not equipment authorization.</p></details>
    {!demo.started ? <p className="task-result">Start the demo incident to assign this observation.</p> : !demo.waiting && <p className="task-result" role="status">{
      latest?.outcome === 'readable' ? 'Local sample: 180 kPa. Cause and recovery remain unverified.'
      : latest?.outcome === 'wrong-equipment' ? 'Identity disputed. Confirm the location before assigning evidence to F-17.'
      : latest?.outcome === 'cannot-access' ? 'Access blocked. No observation was made; agree on a safe alternative.'
      : 'Reading unknown. Another observation is needed; no value was invented.'
    }</p>}
    <button className="button primary wide" onClick={goOperator}>Open operator task <Icon name="arrow" size={18} /></button>
    {demo.started && !demo.waiting && <button className="button secondary wide repeat-observation" onClick={reopen}>Request another observation</button>}
    <p className="caption">Same tab only · Live AI not connected</p>
  </section>;
}
