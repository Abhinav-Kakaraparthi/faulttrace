import { useEffect, useRef, useState, useSyncExternalStore } from 'react';
import { AccessSession } from './access';
import { ConnectedWorkspace } from './Connected';
import { demoSessionRequest, type DemoSession } from './demoSession';
import type { Workspace } from './routing';
import './demo-access.css';

export function DemoExperience({ workspace, navigate }: { workspace: Workspace; navigate: (href: string) => void }) {
  const [session, setSession] = useState<DemoSession | null>(null);
  const [loading, setLoading] = useState(true), [error, setError] = useState('');
  const active = useRef<AccessSession | null>(null);
  const pendingKey = useRef({ start: crypto.randomUUID(), restart: crypto.randomUUID(), end: crypto.randomUUID() });
  useEffect(() => {
    let mounted = true;
    demoSessionRequest().then(value => { if (mounted) setSession(value); })
      .catch(() => { if (mounted) setError('Session unavailable or expired. Choose Try demo; previous investigations are retained.'); })
      .finally(() => { if (mounted) setLoading(false); });
    return () => { mounted = false; active.current?.logout(''); };
  }, []);
  async function change(operation: 'start' | 'restart' | 'end') {
    if (loading) return;
    setLoading(true); setError(''); active.current?.logout('');
    try {
      const current = operation === 'start' ? await demoSessionRequest() : session;
      if (!current) throw new Error('Choose Try demo to begin.');
      const next = await demoSessionRequest(operation, current, pendingKey.current[operation]);
      pendingKey.current[operation] = crypto.randomUUID();
      setSession(operation === 'end' ? null : next);
    } catch (failure) { setError(failure instanceof Error ? failure.message : 'Demo request failed. Refresh before another action.'); }
    finally { setLoading(false); }
  }
  if (loading) return <main className="access-screen" id="main-content" role="status"><h1>Preparing your demo…</h1><p>Simulation only. No provider request.</p></main>;
  return <>
    {session?.active_run ? <DemoWorkspace key={`${session.active_run}-${workspace}`} session={session} workspace={workspace} navigate={navigate}
      register={value => { active.current = value; }} resume={() => void change('start')} restart={() => void change('restart')} end={() => void change('end')} />
      : <DemoEntry live={session?.inference_enabled} error={error} start={() => void change('start')} />}
    {session?.active_run && error && <p role="alert" className="connection-warning">{error}</p>}
  </>;
}

export function DemoEntry({ error, start, live = false }: { error: string; start: () => void; live?: boolean }) {
  return <main className="access-screen demo-entry" id="main-content"><section className="section-surface">
    <span className="eyebrow">FAULTTRACE / SIMULATED EQUIPMENT</span><h1>Trace the cause. Verify the recovery.</h1>
    <p>Explore a private simulated investigation. Switch between Commander and Operator; no account or access token required.</p>
    <button className="button primary" onClick={start}>Try demo</button>
    <p>One demo visitor may use both workspaces. This is not production separation between employees. {live ? 'Live NVIDIA inference is enabled only on explicit actions, within server-wide and session allowances. No automatic retries.' : 'NVIDIA inference is disabled; observations are application-template assignments, not model output.'}</p>
    <p>{live ? 'Photographic interpretations are unverified model claims, not verified readings. Independent compatible human evidence is required for simulated correction.' : 'Photographs are collection-only here. Unreviewed photos can block correction. Explore report-only simulated recovery in a fresh investigation; no image reading is invented.'}</p>
    <details><summary>Demo session and access limits</summary><p>Two-hour absolute expiry, up to three retained investigations per session. Restart creates a new investigation without deleting history. This browser shares the session across tabs. Administrative bearer access is a separate service.</p></details>
    {error && <p role="alert">{error}</p>}
  </section></main>;
}

function DemoWorkspace({ session, workspace, navigate, register, resume, restart, end }: {
  session: DemoSession; workspace: Workspace; navigate: (href: string) => void;
  register: (access: AccessSession) => void; resume: () => void; restart: () => void; end: () => void;
}) {
  const [access] = useState(() => new AccessSession('demo', { demo: {
    workspace, run: session.active_run!, csrf: session.csrf_token } }));
  const [attempted, setAttempted] = useState(false);
  const snapshot = useSyncExternalStore(access.subscribe, access.snapshot, access.snapshot);
  useEffect(() => {
    let mounted = true;
    register(access); void access.authenticate().finally(() => { if (mounted) setAttempted(true); });
    const expiry = setTimeout(() => access.logout('Demo session expired. Choose Try demo; previous investigations are retained.'),
      Math.max(0, session.expires_at * 1000 - Date.now()));
    return () => { mounted = false; clearTimeout(expiry); access.logout(''); };
  }, [access]);
  if (!attempted || snapshot.status === 'checking') return <main className="access-screen" id="main-content" role="status"><h1>Opening your demo workspace…</h1><p>Simulation only; inference disabled.</p></main>;
  if (snapshot.status !== 'ready') return <DemoEntry live={session.inference_enabled} error={snapshot.message}
    start={resume} />;
  return <><div className="access-toolbar workspace-access-toolbar demo-toolbar">
    <strong>Demo visitor · both workspaces</strong><span>{session.inference_enabled ? 'Live inference · bounded explicit actions' : 'Inference disabled'}</span>
    <a href="/operator" target="_blank" rel="noopener">Operator in second tab</a>
    <button className="button secondary" onClick={restart}>Restart demo</button>
    <button className="button quiet" onClick={end}>End demo</button>
    <details><summary>Session limits</summary><p>Expires {new Date(session.expires_at * 1000).toLocaleString()}. One visitor controls both views. Restart retains previous investigations.</p></details>
  </div><ConnectedWorkspace access={access} workspace={workspace} navigate={navigate} /></>;
}
