import { useEffect, useRef, useState } from 'react';
import type { ServerEvidence } from './api';
import type { Workspace } from './routing';
import { useWorkflow } from './useWorkflow';
import { CommanderPage } from './CommanderPage';
import { OperatorPage } from './OperatorPage';
import { ServerEvidenceDetails } from './ServerEvidence';
import { Icon } from './Icon';
import './workspaces.css';

export function Connected({ workspace, navigate }: { workspace: Workspace; navigate: (href: string) => void }) {
  // One controller per mounted connected app. Pages never maintain a second incident/task store.
  const server = useWorkflow();
  const [inspected, inspect] = useState<ServerEvidence | null>(null);
  const dialog = useRef<HTMLDialogElement>(null);
  const focusReturn = useRef<HTMLElement | null>(null);
  useEffect(() => { if (inspected) dialog.current?.showModal(); }, [inspected]);
  useEffect(() => { dialog.current?.close(); inspect(null); }, [workspace]);
  function open(item: ServerEvidence) { focusReturn.current = document.activeElement as HTMLElement; inspect(item); }
  function close() { dialog.current?.close(); inspect(null); focusReturn.current?.focus(); }
  const state = server.state;
  const props = { state, connection: server.connection, disabled: server.busy || server.connection !== 'online',
    mutate: server.mutate, navigate, inspect: open,
    analyze: (item: ServerEvidence) => {
      if (state?.task && state.task.id === item.task_id) {
        const photo = item.status === 'collected';
        void server.mutate(`/api/evidence/${item.id}/${photo ? 'analyze-photo' : 'analyze'}`, { revision: state.task.revision }, `${photo ? 'photo-analysis' : 'analysis'}-${item.id}-${state.task.revision}`);
      }
    } };
  const link = (value: Workspace) => <a key={value} href={`/${value}`} aria-current={workspace === value ? 'page' : undefined}
    onClick={e => { if (e.button === 0 && !e.ctrlKey && !e.metaKey && !e.shiftKey && !e.altKey) { e.preventDefault(); navigate(`/${value}`); } }}><Icon name={value === 'commander' ? 'grid' : 'phone'} />{value === 'commander' ? 'Commander' : 'Operator'}</a>;
  return <div className={`app-shell connected-shell ${workspace}-workspace`}><a className="skip-link" href="#main-content">Skip to workspace</a>
    <aside className="sidebar"><div className="brand"><span className="brand-mark"><Icon name="trace" /></span>FaultTrace.</div><p className="tagline">Trace the cause.<br />Verify the recovery.</p><nav aria-label="Workspaces">{(['commander', 'operator'] as const).map(link)}</nav><div className="sidebar-bottom"><strong>Local server workflow</strong><span>Shared SQLite incident</span><span>Routes are not authenticated roles</span></div></aside>
    <div className="workspace"><div className="demo-banner"><span>Simulated incident / local server</span><span>Inference only on explicit opt-in</span></div>
      <header className="topbar"><span className="mobile-brand">FaultTrace.</span><span>Server: {server.connection === 'online' ? 'connected locally' : server.connection === 'loading' ? 'loading' : 'unavailable / polling paused'}</span><button className="button quiet" onClick={server.refresh}>Refresh server state</button></header>
      <nav className="mobile-switch" aria-label="Workspaces">{(['commander', 'operator'] as const).map(link)}</nav>
      {server.connection === 'paused' && <p className="connection-warning" role="status">Connection interrupted. Displayed state may be stale; writes are disabled. Refresh to reconnect. No request is automatically retried.</p>}
      {server.error && <p className="connection-warning" role="alert">{server.error}</p>}
      {workspace === 'commander' ? <CommanderPage {...props} /> : <OperatorPage {...props} />}
    </div>
    <dialog ref={dialog} className="evidence-dialog" aria-label="Evidence inspection" onCancel={e => { e.preventDefault(); close(); }} onClose={() => inspect(null)}><div className="dialog-heading"><h2>Stored evidence / provenance</h2><button className="icon-button" aria-label="Close evidence inspection" onClick={close}><Icon name="close" /></button></div>{inspected && <ServerEvidenceDetails evidence={state?.evidence.find(e => e.id === inspected.id) ?? inspected} />}</dialog>
  </div>;
}
