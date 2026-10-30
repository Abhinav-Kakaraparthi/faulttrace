import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { PhotoCapture, PhotoDraft } from '../src/PhotoCapture';
import { Connected, ConnectedWorkspace } from '../src/Connected';
import { AccessSession } from '../src/access';
import { TokenEntry, WrongWorkspace } from '../src/AccessGate';
import { SessionToolbar } from '../src/SessionToolbar';
import { DemoEntry } from '../src/DemoExperience';
export { demoSessionRequest } from '../src/demoSession';
export { AccessSession } from '../src/access';
export { configuredProfile, validateIdentity, canCreate, workspaceAllowed } from '../src/identity';
export { APIError } from '../src/api';
export { WorkflowController } from '../src/workflowController';
export { synchronizeInspectionDialog } from '../src/inspectionDialog';
import { ServerEvidenceDetails } from '../src/ServerEvidence';
import { CommanderPage } from '../src/CommanderPage';
import { OperatorPage } from '../src/OperatorPage';
import { JourneyPanel } from '../src/JourneyPanel';
import { PlannerPanel } from '../src/PlannerPanel';
import { AuditHistory } from '../src/AuditHistory';
import { ServerEvidenceList } from '../src/ServerEvidence';
import type { ServerState } from '../src/api';

export const renderJourney = (state: ServerState, view: 'commander' | 'operator') =>
  renderToStaticMarkup(createElement(JourneyPanel, { state, view, disabled: false, mutate: async () => true }));
export const renderEvidence = (state: ServerState) =>
  renderToStaticMarkup(createElement(ServerEvidenceList, { state, disabled: false, inspect: () => {}, analyze: () => {} }));
export const renderPlanningHistory = (state: ServerState) =>
  renderToStaticMarkup(createElement(PlannerPanel, { state, disabled: false, choose: () => {}, open: () => {}, historyOnly: true }));
export const renderPlanner = (state: ServerState) =>
  renderToStaticMarkup(createElement(PlannerPanel, { state, disabled: false, choose: () => {}, open: () => {} }));
export const renderAudit = (state: ServerState) =>
  renderToStaticMarkup(createElement(AuditHistory, { state }));

const pageProps = (state: ServerState | null, overrides = {}) => ({ state, connection: 'online' as const, disabled: false,
  mutate: async () => true, inspect: () => {}, analyze: () => {}, navigate: () => {}, ...overrides });
export const renderCommander = (state: ServerState | null, overrides = {}) =>
  renderToStaticMarkup(createElement(CommanderPage, pageProps(state, overrides)));
export const renderOperator = (state: ServerState | null, overrides = {}) =>
  renderToStaticMarkup(createElement(OperatorPage, pageProps(state, overrides)));

export const renderPhotoCapture = (supported = true) => renderToStaticMarkup(createElement(PhotoCapture, {
  asset: 'V-08', disabled: false, supported, upload: async () => true }));
export const renderPhotoDraft = (overrides = {}) => renderToStaticMarkup(createElement(PhotoDraft, {
  url: 'blob:actual-local-selection', busy: false, progress: null, ready: true, failed: false,
  onReplace: () => {}, onCancel: () => {}, onSubmit: () => {}, ...overrides }));
export const renderEvidenceDetails = (evidence: ServerState['evidence'][number]) =>
  renderToStaticMarkup(createElement(ServerEvidenceDetails, { evidence }));
// Existing workspace assertions exercise the explicit-local shell; the locked
// release entry is covered separately. No live server or provider is involved.
export const renderConnected = () => {
  const access = new AccessSession('local');
  access.snapshot = () => ({ epoch: 1, status: 'ready', message: '', identity: { profile: 'local', principal_id: null, role: null, capabilities: { create_incident: false }, incident_ids: [] } });
  return renderToStaticMarkup(createElement(ConnectedWorkspace, { access, workspace: 'operator', navigate: () => {} }));
};
export const renderLocked = () => renderToStaticMarkup(createElement(Connected, { workspace: 'commander', navigate: () => {} }));
export const renderTokenEntry = (checking = false) => renderToStaticMarkup(createElement(TokenEntry, { checking, message: '', local: false, authenticate: async () => false }));
export const renderWrongWorkspace = (role: 'commander' | 'operator') => renderToStaticMarkup(createElement(WrongWorkspace, { role, navigate: () => {} }));
export const renderSessionToolbar = () => renderToStaticMarkup(createElement(SessionToolbar, {
  identity: { profile: 'release', principal_id: 'field-review', role: 'operator', capabilities: { create_incident: false }, incident_ids: [] },
  aligned: true, refresh: () => {}, logout: () => {} }));
export const renderDemoEntry = (live = false) => renderToStaticMarkup(createElement(DemoEntry, { error: '', start: () => {}, live }));
