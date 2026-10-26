import type { ServerEvidence } from './api';

export const statusLabel: Record<string, string> = {
  collected: 'Photograph collected / not analyzed', pending: 'Image accepted · not analyzed',
  accepted: 'Accepted model interpretation', unreadable: 'Unreadable · clearer evidence needed',
  refused: 'Operator refusal', failed: 'Analysis failed · no automatic retry',
  stale: 'Stale evidence · superseded task', uncertain: 'Uncertain · analysis interrupted',
};

export function evidenceStatus(item: ServerEvidence) {
  if (item.kind === 'report' && item.status === 'accepted') return 'Accepted human report · not image-verified';
  if (item.analysis?.contract === 'photo-observation-v1') return `Photographic analysis / ${item.analysis.status}`;
  return item.analysis?.status === 'pending' ? 'Analysis pending · no reading yet' : statusLabel[item.status] ?? item.status;
}

export function evidenceTimestamp(value: string) {
  if (typeof value !== 'string' || !value.trim()) return 'Timestamp unavailable';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? 'Timestamp unavailable' : new Intl.DateTimeFormat('en-GB', {
    dateStyle: 'medium', timeStyle: 'medium', timeZone: 'UTC',
  }).format(date) + ' UTC';
}
