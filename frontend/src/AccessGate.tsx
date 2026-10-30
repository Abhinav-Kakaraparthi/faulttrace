import { useEffect, useState, useSyncExternalStore, type ReactNode } from 'react';
import { AccessSession } from './access';
import { configuredProfile, workspaceAllowed } from './identity';
import type { Workspace } from './routing';
import { SessionToolbar } from './SessionToolbar';
import './access.css';

export function TokenEntry({ checking, message, local, authenticate }: {
  checking: boolean; message: string; local: boolean; authenticate: (token: string) => Promise<boolean>;
}) {
  const [token, setToken] = useState('');
  async function submit() {
    const candidate = token; setToken(''); await authenticate(candidate);
  }
  return <main id="main-content" tabIndex={-1} className="access-screen">
    <section className="section-surface"><span className="eyebrow">FAULTTRACE / SIMULATION ONLY</span>
      <h1>{local ? 'Verify explicit local access' : 'Enter workspace access token'}</h1>
      <p>{local ? 'Local mode requires the server to confirm its explicit local identity. It never falls back from release authentication.' : 'Use the credential delivered privately by your administrator. Your role and incident access are verified by the server.'}</p>
      <form onSubmit={event => { event.preventDefault(); if (!checking) void submit(); }} autoComplete="off">
        {!local && <label htmlFor="access-token">Access token<input id="access-token" name="access-token" type="password" value={token} onChange={event => setToken(event.target.value)} autoComplete="off" autoCapitalize="none" spellCheck={false} required disabled={checking} aria-describedby="access-help" /></label>}
        <button className="button primary" disabled={checking || (!local && !token)}>{checking ? 'Verifying identity…' : local ? 'Verify local server' : 'Open authorized workspace'}</button>
      </form>
      <p id="access-help">Tokens remain in memory only. Reload requires re-entry. Browser logout clears access but does not revoke the credential. Interrupted writes may have reached the server; they are never automatically replayed.</p>
      <p role="status">{checking ? 'Verifying identity before loading private state.' : message}</p>
      <a href="/?mode=sample">Open separate sample preview</a>
    </section>
  </main>;
}

export function WrongWorkspace({ role, navigate }: { role: 'commander' | 'operator'; navigate: (href: string) => void }) {
  return <main id="main-content" tabIndex={-1} className="access-screen"><section className="section-surface" role="status"><h1>Wrong workspace</h1>
    <p>Your authenticated role is {role}. This route grants no additional authority.</p>
    <button className="button primary" onClick={() => navigate(`/${role}`)}>Open {role === 'commander' ? 'Commander' : 'Operator'} workspace</button>
  </section></main>;
}

export function AccessGate({ workspace, navigate, children }: {
  workspace: Workspace; navigate: (href: string) => void; children: (access: AccessSession, controls: ReactNode) => ReactNode;
}) {
  const [configuration] = useState(() => {
    try { return { access: new AccessSession(configuredProfile(import.meta.env.VITE_FAULTTRACE_PROFILE)), error: '' }; }
    catch { return { access: null, error: 'Invalid access profile configuration. Use release or explicit local.' }; }
  });
  if (!configuration.access) return <main className="access-screen" id="main-content"><h1>Access configuration unavailable</h1><p role="alert">{configuration.error}</p></main>;
  return <AccessBoundary access={configuration.access} workspace={workspace} navigate={navigate}>{children}</AccessBoundary>;
}

function AccessBoundary({ access, workspace, navigate, children }: {
  access: AccessSession; workspace: Workspace; navigate: (href: string) => void; children: (access: AccessSession, controls: ReactNode) => ReactNode;
}) {
  const snapshot = useSyncExternalStore(access.subscribe, access.snapshot, access.snapshot);
  useEffect(() => () => access.logout(''), [access]);
  useEffect(() => {
    if (snapshot.status !== 'checking') document.getElementById('main-content')?.focus();
  }, [snapshot.epoch, snapshot.status, workspace]);
  const identity = snapshot.identity;
  const aligned = snapshot.status === 'ready' && !!identity && workspaceAllowed(identity, workspace);
  const controls = <SessionToolbar identity={identity} aligned={false}
    refresh={() => void access.refreshIdentity()} logout={() => access.logout()} />;
  return <>
    {snapshot.status !== 'locked' && !aligned && controls}
    {snapshot.status !== 'ready' || !identity
      ? <TokenEntry key={snapshot.epoch} local={access.profile === 'local'} checking={snapshot.status === 'checking'} message={snapshot.message} authenticate={token => access.authenticate(token)} />
      : !workspaceAllowed(identity, workspace)
        ? <WrongWorkspace role={identity.role!} navigate={navigate} />
        : <div key={snapshot.epoch}>{children(access, controls)}</div>}
  </>;
}
