import type { Identity } from './identity';

// Presentation only: the boundary owns identity, refresh and logout behavior.
export function SessionToolbar({ identity, aligned, refresh, logout }: {
  identity: Identity | null; aligned: boolean; refresh: () => void; logout: () => void;
}) {
  return <div className={`access-toolbar${aligned ? ' workspace-access-toolbar' : ''}`} aria-label="Session access">
    {identity ? <details className="session-identity"><summary>
      <strong>{identity.role === 'commander' ? 'Commander' : identity.role === 'operator' ? 'Operator' : 'Local workspaces'}</strong>
      <span className="session-principal">{identity.profile} / {identity.principal_id ?? 'explicit local identity'}</span>
    </summary><div className="session-identity-body"><p>Profile: {identity.profile}. Principal: {identity.principal_id ?? 'explicit local identity'}.</p>
      <p>Browser logout clears access; it does not revoke the credential.</p></div></details> : <span>Verifying access</span>}
    <button className="button secondary" aria-label="Refresh access" disabled={!identity} onClick={refresh}>Refresh access</button>
    <button className="button quiet" onClick={logout}>Log out</button>
  </div>;
}
