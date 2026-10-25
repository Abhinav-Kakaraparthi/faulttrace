import type { WorkspaceProps } from './workspace';
import { JourneyRecord } from './JourneyRecord';
import { ServerEvidenceList } from './ServerEvidence';

export function EvidenceWorkspace({ state, inspect, analyze, disabled, workspace }: WorkspaceProps & { workspace: 'commander' | 'operator' }) {
  if (!state?.incident) return null;
  const journey = state.journey;
  return <section className="workspace-evidence" aria-labelledby="investigation-evidence-title">
    <h2 id="investigation-evidence-title">Investigation evidence</h2>
    <p>Stored sources from this incident. Simulated human reports, uploaded images and NVIDIA interpretations retain their own provenance.</p>
    {journey && <div className="journey"><JourneyRecord journey={journey} completed={journey.maintenance_status !== 'not_completed'} /></div>}
    {!!state.evidence.length && <ServerEvidenceList state={state} inspect={inspect} analyze={analyze} disabled={disabled} allowAnalysis={workspace === 'operator'} />}
    {!state.evidence.length && !journey && <section className="section-surface connected-empty"><h3>No observation evidence yet</h3><p>Operator submissions will appear here. No reading, model interpretation or cause has been established.</p></section>}
    {!state.evidence.length && journey && <p className="caption">No image or NVIDIA planner-task evidence in this run. The journey records above are simulated observations, not missing uploads.</p>}
    {journey && !!state.evidence.length && <p className="notice">NVIDIA task evidence is available for investigation, but it is not consumed by the simulated correction/recovery assessment. That workflow currently checks its own simulated human reports and simulator samples.</p>}
  </section>;
}
