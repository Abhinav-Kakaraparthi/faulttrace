import { APIError, apiResponse, type ServerState } from './api';
import { validateIdentity, type Identity, type Profile } from './identity';
import { localPhotoURL, MAX_PHOTO_BYTES, uploadBlob, type UploadProgress } from './photoUpload';

export type AccessSnapshot = { epoch: number; status: 'locked' | 'checking' | 'ready'; identity: Identity | null; message: string };
type Dependencies = { fetch: typeof fetch; upload: typeof uploadBlob; urls: Pick<typeof URL, 'createObjectURL' | 'revokeObjectURL'>;
  demo?: { workspace: 'commander' | 'operator'; run: string; csrf: string } };
const interrupted = () => new DOMException('Access changed or response interrupted. Writes may have reached the server; refresh before acting.', 'AbortError');

// One instance per connected application. Private fields never enter React props,
// snapshots, URLs or persistence. All asynchronous reads remain epoch-bound.
export class AccessSession {
  #token = '';
  #snapshot: AccessSnapshot = { epoch: 0, status: 'locked', identity: null, message: '' };
  #listeners = new Set<() => void>();
  #pending = new Map<AbortController, number>();
  #images = new Map<string, { url: string; release: () => void }>();
  #dependencies: Dependencies;
  constructor(readonly profile: Profile, dependencies: Partial<Dependencies> = {}) {
    this.#dependencies = { fetch: (...args) => fetch(...args), upload: uploadBlob, urls: URL, ...dependencies };
  }
  snapshot = () => this.#snapshot;
  subscribe = (listener: () => void) => { this.#listeners.add(listener); return () => { this.#listeners.delete(listener); }; };
  current(epoch: number) { return epoch === this.#snapshot.epoch && this.#snapshot.status === 'ready'; }
  #publish(value: AccessSnapshot) { this.#snapshot = value; this.#listeners.forEach(listener => listener()); }
  releaseImages(epoch = this.#snapshot.epoch) {
    if (epoch !== this.#snapshot.epoch) return;
    this.#images.forEach(image => image.release()); this.#images.clear();
  }
  cancelPending(epoch = this.#snapshot.epoch) { this.#pending.forEach((owner, controller) => { if (owner === epoch) controller.abort(); }); }
  logout = (message = 'Browser access cleared. This does not revoke the credential. Pending writes may have reached the server; none will be replayed.') => {
    this.#token = '';
    const epoch = this.#snapshot.epoch + 1;
    // Invalidate before abort callbacks can settle.
    this.#snapshot = { epoch, status: 'locked', identity: null, message };
    this.#pending.forEach((_owner, controller) => controller.abort()); this.#pending.clear();
    this.releaseImages(); this.#publish(this.#snapshot);
  };
  async authenticate(token = ''): Promise<boolean> {
    this.logout('');
    const epoch = this.#snapshot.epoch;
    if (this.profile === 'release' && (!token || /\s/.test(token))) {
      this.logout('Enter a valid access token.'); return false;
    }
    this.#token = this.profile === 'release' ? token : '';
    this.#publish({ epoch, status: 'checking', identity: null, message: '' });
    try {
      const value = await this.#request('/api/identity', {}, response => apiResponse(response), undefined, true);
      const identity = validateIdentity(value, this.profile);
      if (epoch !== this.#snapshot.epoch) return false;
      this.#publish({ epoch, status: 'ready', identity, message: '' }); return true;
    } catch (failure) {
      if (epoch === this.#snapshot.epoch) this.logout(failure instanceof Error && failure.name !== 'AbortError'
        ? failure.message : 'Identity could not be verified. Access remains closed.');
      return false;
    }
  }
  refreshIdentity = () => this.authenticate(this.#token);
  async #request<T>(path: string, init: RequestInit, read: (response: Response) => Promise<T>, progress?: UploadProgress, identity = false): Promise<T> {
    const epoch = this.#snapshot.epoch;
    if ((!identity && !this.current(epoch)) || !/^\/api\/[A-Za-z0-9/_-]+$/.test(path)) throw interrupted();
    const controller = new AbortController(); this.#pending.set(controller, epoch);
    const abort = () => controller.abort();
    init.signal?.addEventListener('abort', abort, { once: true });
    if (init.signal?.aborted) controller.abort();
    const timeout = setTimeout(abort, init.method === 'POST' ? 15000 : 5000);
    const valid = () => { if (controller.signal.aborted || epoch !== this.#snapshot.epoch) throw interrupted(); };
    try {
      valid();
      const headers = new Headers(init.headers);
      headers.delete('Authorization'); headers.delete('X-FaultTrace-Local');
      if (this.profile === 'release') headers.set('Authorization', `Bearer ${this.#token}`);
      else if (this.profile === 'demo') {
        const demo = this.#dependencies.demo;
        if (!demo) throw new Error('Demo configuration unavailable.');
        headers.set('X-FaultTrace-Demo', '1'); headers.set('X-FaultTrace-Workspace', demo.workspace);
        headers.set('X-FaultTrace-Demo-Run', demo.run);
        if (init.method === 'POST') headers.set('X-CSRF-Token', demo.csrf);
      } else if (init.method === 'POST') headers.set('X-FaultTrace-Local', '1');
      const response = progress && init.body instanceof Blob
        ? await this.#dependencies.upload(path, init.body, Object.fromEntries(headers), controller.signal,
            value => { if (this.current(epoch) && !controller.signal.aborted) progress(value); })
        : await this.#dependencies.fetch(path, { ...init, headers, cache: 'no-store', credentials: this.profile === 'demo' ? 'same-origin' : 'omit', redirect: 'error', signal: controller.signal });
      valid();
      if (response.status === 401) {
        this.logout(this.profile === 'demo' ? 'Demo session expired or ended. Choose Try demo to continue; no write was replayed.' : 'Access ended. Enter your token again. Pending writes may have reached the server; none will be replayed.');
        throw interrupted();
      }
      // Only fixed application errors may be displayed; never surface arbitrary
      // transport messages, response bodies, URLs or reflected credentials.
      if (!response.ok) await apiResponse(response);
      const value = await read(response); valid(); return value;
    } catch (failure) {
      valid();
      if (failure instanceof Error && failure.name === 'AbortError') throw interrupted();
      if (failure instanceof APIError) {
        if (this.profile === 'demo' && failure.code === 'demo_session_changed') {
          this.logout('This demo changed in another tab. Resume the current session; no write was replayed.');
          throw interrupted();
        }
        throw failure;
      }
      throw new Error('Server response unavailable. State may have changed; refresh before another action.');
    } finally {
      clearTimeout(timeout); this.#pending.delete(controller); init.signal?.removeEventListener('abort', abort);
    }
  }
  json(path: string, init: RequestInit = {}, progress?: UploadProgress) {
    return this.#request(path, init, response => apiResponse(response), progress);
  }
  async mutate(path: string, body: object | Blob, key: string, extra: Record<string, string> = {}, progress?: UploadProgress) {
    if (!/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/.test(key)) throw new Error('Invalid request identifier.');
    if (body instanceof Blob && (!body.size || body.size > MAX_PHOTO_BYTES || !['image/png', 'image/jpeg'].includes(body.type))) throw new Error('Choose a PNG/JPEG image no larger than 2 MiB.');
    return this.json(path, { method: 'POST', headers: { ...extra, 'Content-Type': body instanceof Blob ? body.type : 'application/json', 'Idempotency-Key': key },
      body: body instanceof Blob ? body : JSON.stringify(body) }, progress);
  }
  async state(signal: AbortSignal): Promise<ServerState> {
    const epoch = this.#snapshot.epoch;
    const value: ServerState = await this.json('/api/state', { signal });
    if (!Array.isArray(value.planning) || typeof value.planning_remaining !== 'number' || !Array.isArray(value.evidence)) throw new Error('Incompatible server state. Access remains restricted.');
    // Ignore server-supplied image URLs. Only canonical, authenticated same-origin
    // image endpoints are read; private state receives temporary blob URLs only.
    const evidence = await Promise.all(value.evidence.map(async item => {
      if (item.kind !== 'image') return item;
      let image = this.#images.get(item.id);
      if (!image) {
        try {
          const blob = await this.#request(`/api/evidence/${encodeURIComponent(item.id)}/image`, { signal }, response => response.blob());
          if (!this.current(epoch) || signal.aborted) throw interrupted();
          image = localPhotoURL(blob, this.#dependencies.urls);
          this.#images.set(item.id, image);
        } catch {
          if (!this.current(epoch) || signal.aborted) throw interrupted();
          return { ...item, image_url: null };
        }
      }
      return { ...item, image_url: image.url };
    }));
    if (!this.current(epoch) || signal.aborted) throw interrupted();
    const retained = new Set(evidence.filter(item => item.kind === 'image').map(item => item.id));
    for (const [id, image] of this.#images) if (!retained.has(id)) { image.release(); this.#images.delete(id); }
    return { ...value, evidence };
  }
}
