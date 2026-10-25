import { httpDiagnosticSummary, type Receipt } from './api';

export function HTTPDiagnostics({ receipt }: { receipt: Receipt }) {
  const summary = httpDiagnosticSummary(receipt);
  return summary === null ? null : <p className="caption">{summary}</p>;
}
