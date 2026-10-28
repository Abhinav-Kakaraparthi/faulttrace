import { useEffect, useId, useMemo, useRef, useState, useSyncExternalStore } from 'react';
import type { AccessSession } from './access';
import './documentation.css';

const manufacturers: Record<string, string> = { 'maximator.de': 'MAXIMATOR', 'maximator.com': 'MAXIMATOR',
  'emerson.com': 'Emerson', 'wika.com': 'WIKA', 'swagelok.com': 'Swagelok' };
type Source = { url: string; title: string; excerpt: string; model_match: string };
type LookupRecord = { id: string; status: string; created_at: string; error: string | null;
  context: { manufacturer: string; model: string; domain: string }; result: { sources: Source[]; usage_credits: number | null; retrieved_at?: string } | null };

export function safeDocumentationURL(address: string, domain: string) {
  try { const url = new URL(address); return url.protocol === 'https:' && !url.username && !url.password
    && (!url.port || url.port === '443') && (url.hostname === domain || url.hostname.endsWith(`.${domain}`)); }
  catch { return false; }
}

export function DocumentationRecords({ records }: { records: LookupRecord[] }) {
  return <div className="documentation-records">{records.length === 0 ? <p>No manufacturer lookup in this investigation.</p>
    : records.map(record => <details key={record.id}><summary>{record.context.manufacturer} {record.context.model} · {record.status}</summary>
      <p className="caption">{record.result?.retrieved_at ? `Retrieved ${new Date(record.result.retrieved_at).toLocaleString()}`
        : `Requested ${new Date(record.created_at).toLocaleString()}`} · restricted to {record.context.domain}</p>
      {record.error && <p role="status">Lookup did not complete successfully. No automatic retry.</p>}
      {record.status === 'stale' && <p>Incident evidence changed during lookup. Reference context is retained; it is not current evidence.</p>}
      {record.result && !record.result.sources.length && <p>No allowlisted manufacturer source returned. Do not assume a document or model match.</p>}
      {record.result?.sources.map((source, index) => <article key={`${record.id}-${index}`}>
        {safeDocumentationURL(source.url, record.context.domain) ? <a href={source.url} target="_blank" rel="noopener noreferrer">{source.title || 'Manufacturer source'}</a> : <span>Source link unavailable</span>}
        <p>{source.excerpt}</p><p className="caption">{source.model_match === 'text_mentions_requested_model'
          ? 'Snippet mentions the requested model; applicability still requires human review.' : 'Model applicability unverified.'}</p>
      </article>)}
      <p className="caption">Untrusted reference material · not telemetry, a measured reading or correction authority.</p>
    </details>)}</div>;
}

export function DocumentationLookup({ access, revision, enabled }: { access: AccessSession; revision: number; enabled: boolean }) {
  const snapshot = useSyncExternalStore(access.subscribe, access.snapshot, access.snapshot);
  const owner = useMemo(() => crypto.randomUUID(), [access]);
  if (snapshot.status !== 'ready') return <section className="section-surface"><h2>Manufacturer documentation</h2><p>Reference access unavailable. No retained source details are displayed.</p></section>;
  return <DocumentationSession key={`${owner}-${snapshot.epoch}`} access={access} revision={revision} enabled={enabled} />;
}

export function documentationRecords(value: unknown, authorized: boolean): LookupRecord[] {
  if (!authorized || !Array.isArray(value)) return [];
  const valid = value.every(record => record && typeof record.id === 'string' && typeof record.status === 'string'
    && typeof record.created_at === 'string' && record.context && typeof record.context.manufacturer === 'string'
    && typeof record.context.model === 'string' && typeof record.context.domain === 'string'
    && (record.result === null || (record.result && Array.isArray(record.result.sources)
      && record.result.sources.every((source: Source) => source && typeof source.url === 'string'
        && typeof source.title === 'string' && typeof source.excerpt === 'string' && typeof source.model_match === 'string'))));
  return valid ? value : [];
}

function DocumentationSession({ access, revision, enabled }: { access: AccessSession; revision: number; enabled: boolean }) {
  const id = useId();
  const [domain, setDomain] = useState('maximator.de'), [model, setModel] = useState('');
  const [confirmed, setConfirmed] = useState(false), [busy, setBusy] = useState(false);
  const [records, setRecords] = useState<LookupRecord[]>([]), [message, setMessage] = useState('');
  const requestKey = useRef(crypto.randomUUID());
  const context = useRef('');
  const mounted = useRef(false);
  const epoch = access.snapshot().epoch;
  useEffect(() => {
    const controller = new AbortController(); mounted.current = true;
    access.json('/api/documentation', { signal: controller.signal }).then(value => {
      if (mounted.current && access.current(epoch)) setRecords(documentationRecords(value.records, true));
    }).catch(() => { if (mounted.current && access.current(epoch)) {
      setRecords([]); setMessage('Reference history unavailable. Refresh access before another action.'); } });
    return () => { mounted.current = false; controller.abort(); };
  }, [access, epoch, revision]);
  async function submit(event: React.FormEvent) {
    event.preventDefault(); if (!confirmed || busy || !enabled || !model.trim()) return;
    const fingerprint = JSON.stringify([domain, model, revision]);
    if (context.current !== fingerprint) { context.current = fingerprint; requestKey.current = crypto.randomUUID(); }
    setBusy(true); setMessage('Searching official manufacturer sources…');
    try {
      await access.mutate('/api/documentation', { manufacturer: manufacturers[domain], model, domain, revision }, requestKey.current);
      const value = await access.json('/api/documentation');
      if (mounted.current && access.current(epoch)) { setRecords(documentationRecords(value.records, true)); setMessage('Lookup recorded. Review source applicability; reference text grants no authority.'); }
    } catch { if (mounted.current && access.current(epoch)) { setRecords([]); setMessage('Lookup unavailable or budget exhausted. No automatic retry; refresh history before acting.'); } }
    finally { if (mounted.current && access.current(epoch)) setBusy(false); }
  }
  return <section className="section-surface documentation-lookup"><h2>Manufacturer documentation</h2>
    <p>Search only after independently confirming the manufacturer and model. Assignment and photograph labels do not prove identity.</p>
    <form onSubmit={event => void submit(event)}><label htmlFor={`${id}-domain`}>Official manufacturer domain</label>
      <select id={`${id}-domain`} value={domain} disabled={busy} onChange={event => { setDomain(event.target.value); setConfirmed(false); }}>
        {Object.entries(manufacturers).map(([address, name]) => <option key={address} value={address}>{name} · {address}</option>)}
      </select><label htmlFor={`${id}-model`}>Human-confirmed equipment model</label>
      <input id={`${id}-model`} value={model} maxLength={80} required disabled={busy} autoComplete="off"
        onChange={event => { setModel(event.target.value); setConfirmed(false); }} />
      <label className="documentation-confirm"><input type="checkbox" checked={confirmed} disabled={busy}
        onChange={event => setConfirmed(event.target.checked)} />I independently confirmed this manufacturer/model; it was not inferred from assignment.</label>
      <button className="button secondary" disabled={!enabled || busy || !confirmed || !model.trim()}>{busy ? 'Lookup pending' : 'Search official documentation'}</button>
      {!enabled && <p className="caption">Documentation lookup is disabled in this offline configuration. No Tavily request will be made.</p>}
    </form><p role="status">{message}</p><DocumentationRecords records={records} />
  </section>;
}
