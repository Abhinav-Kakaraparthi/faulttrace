import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
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
