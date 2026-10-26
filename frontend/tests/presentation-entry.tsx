import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { PhotoCapture, PhotoDraft } from '../src/PhotoCapture';
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
