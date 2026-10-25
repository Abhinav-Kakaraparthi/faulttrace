import type { WorkspaceProps } from './workspace';

export function WorkspaceState({ state, connection, workspace }: Pick<WorkspaceProps, 'state' | 'connection'> & { workspace: 'commander' | 'operator' }) {
  if (!state) return <section className="section-surface connected-empty" role="status">
    <h2>{connection === 'loading' ? 'Loading server state' : 'Backend is not available'}</h2>
    <p>{connection === 'loading' ? 'Waiting for the shared incident and assignments.' : 'Displayed state cannot be loaded. Use Refresh server state to reconnect; no sample result is substituted.'}</p>
  </section>;
  if (!state.incident) return <section className="section-surface connected-empty">
    <h2>{workspace === 'operator' ? 'Waiting for an assignment' : 'Ready for a simulated investigation'}</h2>
    <p>{workspace === 'operator' ? 'Commander must start an incident and assign an observation. No operator task or correction is authorized yet.' : 'Start an isolated simulation or an observation-only incident. Existing records are preserved; no cause is preselected.'}</p>
  </section>;
  return null;
}
