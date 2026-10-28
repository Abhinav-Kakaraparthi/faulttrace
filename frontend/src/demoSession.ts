import { apiResponse } from './api';
export type DemoSession = { active_run: string | null; csrf_token: string; expires_at: number;
  inference_enabled: boolean; privileges: string };
let bootstrap: Promise<DemoSession> | null = null;
export function demoSessionRequest(operation = 'session', session?: DemoSession, key?: string): Promise<DemoSession> {
  // StrictMode's repeated mount and same-tab consumers share the cookie bootstrap.
  if (operation === 'session') {
    bootstrap ??= request(operation).finally(() => { bootstrap = null; });
    return bootstrap;
  }
  return request(operation, session, key);
}
async function request(operation: string, session?: DemoSession, key?: string): Promise<DemoSession> {
  const headers: Record<string, string> = { 'X-FaultTrace-Demo': '1' };
  if (operation !== 'session') {
    if (!session || !key) throw new Error('Demo session unavailable.');
    Object.assign(headers, { 'Content-Type': 'application/json', 'X-CSRF-Token': session.csrf_token,
      'X-FaultTrace-Demo-Run': session.active_run ?? '', 'Idempotency-Key': key });
  }
  let response: Response;
  try {
    response = await fetch('/api/demo/' + operation, { method: operation === 'session' ? 'GET' : 'POST',
      headers, credentials: 'same-origin', cache: 'no-store', redirect: 'error', signal: AbortSignal.timeout(10000),
      body: operation === 'session' ? undefined : '{}' });
  } catch { throw new Error('Demo server unavailable. Refresh before another action; no request was retried.'); }
  const value = await apiResponse(response);
  if (operation === 'end') return session!;
  if (!value || typeof value.csrf_token !== 'string' || !/^[A-Za-z0-9_-]{43}$/.test(value.csrf_token) ||
      typeof value.expires_at !== 'number' || !Number.isFinite(value.expires_at) || value.expires_at <= 0 || typeof value.inference_enabled !== 'boolean' ||
      (value.active_run !== null && (typeof value.active_run !== 'string' || !/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/.test(value.active_run))))
    throw new Error('Demo configuration unavailable.');
  return value;
}
