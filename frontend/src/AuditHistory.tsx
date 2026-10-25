import type { ServerState } from './api';

export function AuditHistory({ state }: { state: ServerState }) {
  const content = <><p>Wall-clock audit times (UTC), oldest first. Simulation measurement timestamps are shown separately with the evidence.</p>
    {!state.events.length ? <p>No audit events recorded.</p> : <ol>{state.events.map(event => <li key={event.sequence}>
      <strong>{event.kind.replaceAll('_', ' ')}</strong>
      <time dateTime={event.created_at}>Wall-clock UTC: {event.created_at}</time>
    </li>)}</ol>}</>;
  return <section className="section-surface connected-events">
    {state.journey ? <details><summary>Wall-clock audit history ({state.events.length})</summary>{content}</details> : <><h2>Server activity / wall-clock audit history</h2>{content}</>}
  </section>;
}
