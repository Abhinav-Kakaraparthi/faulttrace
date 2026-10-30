import type { ReactNode } from 'react';
import type { Identity } from './identity';
import type { Workspace } from './routing';
import { Icon } from './Icon';

export function WorkspaceMasthead({ identity, workspace, navigate, controls }: {
  identity: Identity; workspace: Workspace; navigate: (href: string) => void; controls?: ReactNode;
}) {
  const views = (['commander', 'operator'] as const).filter(view => identity.profile !== 'release' || identity.role === view);
  return <header className="workspace-masthead">
    <div className="masthead-brand"><span className="brand-mark"><Icon name="trace" /></span><div><strong>FaultTrace<span>.</span></strong><small>Trace the cause. Verify the recovery.</small></div></div>
    <nav aria-label="Workspaces">{views.map(view => <a key={view} href={`/${view}`} aria-current={workspace === view ? 'page' : undefined}
      onClick={event => { if (event.button === 0 && !event.ctrlKey && !event.metaKey && !event.shiftKey && !event.altKey) { event.preventDefault(); navigate(`/${view}`); } }}>
      <Icon name={view === 'commander' ? 'grid' : 'phone'} />{view === 'commander' ? 'Commander' : 'Operator'}</a>)}</nav>
    {controls && <div className="masthead-session">{controls}</div>}
  </header>;
}
