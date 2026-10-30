import { useEffect, useRef, type ReactNode } from 'react';
import type { ServerEvidence } from './api';
import type { Workspace } from './routing';
import { useWorkflow } from './useWorkflow';
import { CommanderPage } from './CommanderPage';
import { OperatorPage } from './OperatorPage';
import { ServerEvidenceDetails } from './ServerEvidence';
import { Icon } from './Icon';
import { AccessGate } from './AccessGate';
import type { AccessSession } from './access';
import { canCreate } from './identity';
import { synchronizeInspectionDialog } from './inspectionDialog';
import { WorkspaceMasthead } from './WorkspaceMasthead';
import './workspaces.css';
import './photo-workflow.css';
import './workspace-chrome.css';
import './investigation-workspace.css';
import './reference-layout.css';

export function Connected({ workspace, navigate }: { workspace: Workspace; navigate: (href: string) => void }) {
  return <AccessGate workspace={workspace} navigate={navigate}>{(access, controls) => <ConnectedWorkspace access={access} workspace={workspace} navigate={navigate} sessionControls={controls} />}</AccessGate>;
}

export function ConnectedWorkspace({ access, workspace, navigate, sessionControls }: { access: AccessSession; workspace: Workspace; navigate: (href: string) => void; sessionControls?: ReactNode }) {
  // One controller per mounted connected app. Pages never maintain a second incident/task store.
  const server = useWorkflow(access);
  const identity = access.snapshot().identity!;
  const inspected = !server.denied ? server.state?.evidence.find(item => item.id === server.inspectionId) : null;
  const dialog = useRef<HTMLDialogElement>(null);
  const focusReturn = useRef<HTMLElement | null>(null);
  useEffect(() => { synchronizeInspectionDialog(dialog.current, !!inspected); }, [inspected]);
  useEffect(() => { dialog.current?.close(); server.inspect(null); }, [workspace, server.inspect]);
  function open(item: ServerEvidence) { focusReturn.current = document.activeElement as HTMLElement; server.inspect(item.id); }
  function close() { dialog.current?.close(); server.inspect(null); focusReturn.current?.focus(); }
  const state = server.state;
  if (!identity) return null;
  const props = { access, state, connection: server.connection, disabled: server.busy || server.connection !== 'online',
    release: identity.profile !== 'local', canCreate: canCreate(identity), creationReady: !server.busy && (server.connection === 'online' || server.denied),
    mutate: server.mutate, submitPhoto: server.submitPhoto, navigate, inspect: open,
    analyze: (item: ServerEvidence) => {
      if (state?.task && state.task.id === item.task_id) {
        const photo = item.status === 'collected';
        void server.mutate(`/api/evidence/${item.id}/${photo ? 'analyze-photo' : 'analyze'}`, { revision: state.task.revision }, `${photo ? 'photo-analysis' : 'analysis'}-${item.id}-${state.task.revision}`);
      }
    } };
  return <div className={`app-shell connected-shell ${workspace}-workspace`}><a className="skip-link" href="#main-content">Skip to workspace</a>
    <WorkspaceMasthead identity={identity} workspace={workspace} navigate={navigate} controls={sessionControls} />
    <div className="workspace"><header className="connected-topbar">
      <div className="workspace-status"><strong>Simulation only</strong><span>{!state ? 'Inference status pending' : state.test_output ? 'No live inference' : state.inference_enabled ? 'Inference: explicit opt-in only' : 'Inference disabled'}</span><span role="status">{server.connection === 'online' ? 'Connected' : server.connection === 'loading' ? 'Loading server' : 'Server unavailable / polling paused'}</span></div>
      <div className="workspace-tools"><button className="button quiet" aria-label="Refresh server state" onClick={server.refresh}>Refresh</button><details className="workspace-info"><summary aria-label="Workspace information">Info</summary><div className="workspace-info-body"><p>Shared SQLite incident. {identity.profile === 'demo' ? 'Only this visitor’s demo is accessible. One visitor uses both workspaces.' : identity.profile === 'release' ? 'Access is checked by the server for every request.' : 'Explicit local mode has no role isolation.'} No real equipment control.</p><a href="/?mode=sample">Open separate sample preview</a></div></details></div>
      </header>
      {server.connection === 'paused' && <p className="connection-warning" role="status">Connection interrupted. Displayed state may be stale; writes are disabled. Refresh to reconnect. No request is automatically retried.</p>}
      {server.error && <p className="connection-warning" role="alert">{server.error}</p>}
      {server.denied && <section className="section-surface" role="status"><h2>Incident access denied</h2><p>{identity.profile === 'demo' ? 'This request is outside your current demo. Resume its current investigation; no private state is displayed.' : 'Ask your administrator to review incident grants and task assignments, then choose Refresh access. No private state is displayed.'}</p></section>}
      {workspace === 'commander' ? <CommanderPage {...props} /> : <OperatorPage {...props} />}
    </div>
    <dialog ref={dialog} className="evidence-dialog" aria-label="Evidence inspection" onCancel={e => { e.preventDefault(); close(); }} onClose={() => { server.inspect(null); if (focusReturn.current?.isConnected) focusReturn.current.focus(); }}><div className="dialog-heading"><h2>Inspect evidence</h2><button autoFocus className="icon-button" aria-label="Close evidence inspection" onClick={close}><Icon name="close" /></button></div><div className="dialog-content">{inspected && <ServerEvidenceDetails key={inspected.id} evidence={inspected} />}</div></dialog>
  </div>;
}
