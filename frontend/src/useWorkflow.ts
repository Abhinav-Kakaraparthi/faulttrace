import { useEffect, useRef, useState } from 'react';
import { apiResponse, type ServerState } from './api';

export function useWorkflow() {
  const [state, setState] = useState<ServerState | null>(null);
  const [connection, setConnection] = useState<'loading' | 'online' | 'paused'>('loading');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [generation, refresh] = useState(0);
  const inFlight = useRef(false);
  const keys = useRef(new Map<string, string>());
  useEffect(() => {
    let stopped = false, failures = 0, attempts = 0;
    let timer: ReturnType<typeof setTimeout>;
    let controller: AbortController;
    async function poll() {
      if (stopped) return;
      controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 5000);
      try {
        const value: ServerState = await apiResponse(await fetch('/api/state', { cache: 'no-store', signal: controller.signal }));
        if (!Array.isArray(value.planning) || typeof value.planning_remaining !== 'number') {
          if (!stopped) { setState(null); setError('Backend is running the earlier workflow version. Restart it manually using the FT-007 guide; the agent has left it untouched.'); }
          throw new Error('incompatible_backend');
        }
        if (!stopped) { setState(value); setConnection('online'); }
        failures = 0;
      } catch {
        failures++;
        if (!stopped) setConnection('paused');
      } finally { clearTimeout(timeout); }
      attempts++;
      if (!stopped && failures < 3 && attempts < 900) timer = setTimeout(poll, 2000);
      else if (!stopped) setConnection('paused');
    }
    void poll();
    return () => { stopped = true; clearTimeout(timer); controller?.abort(); };
  }, [generation]);

  async function mutate(path: string, body: object | Blob, identity: string, extra: Record<string, string> = {}) {
    if (inFlight.current) return false;
    inFlight.current = true; setBusy(true); setError('');
    if (!keys.current.has(identity)) keys.current.set(identity, crypto.randomUUID());
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 15000);
    try {
      await apiResponse(await fetch(path, {
        method: 'POST', signal: controller.signal,
        headers: { 'X-FaultTrace-Local': '1', 'Idempotency-Key': keys.current.get(identity)!,
          'Content-Type': body instanceof Blob ? body.type : 'application/json', ...extra },
        body: body instanceof Blob ? body : JSON.stringify(body),
      }));
      refresh(value => value + 1);
      return true;
    } catch (failure) {
      setError(failure instanceof Error && failure.name !== 'AbortError' ? failure.message : 'Response interrupted. State may have changed; refresh before any further action.');
      refresh(value => value + 1);
      return false;
    } finally { clearTimeout(timeout); inFlight.current = false; setBusy(false); }
  }
  return { state, connection, error, busy, mutate, refresh: () => { setError(''); refresh(value => value + 1); } };
}
