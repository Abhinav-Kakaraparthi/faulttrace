import { APIError, type ServerState } from './api';
import type { AccessSession } from './access';
import type { UploadProgress } from './photoUpload';

type Snapshot = { state: ServerState | null; connection: 'loading' | 'online' | 'paused'; error: string; denied: boolean; busy: boolean; inspectionId: string | null };
export class WorkflowController {
  #value: Snapshot = { state: null, connection: 'loading', error: '', denied: false, busy: false, inspectionId: null };
  #listeners = new Set<() => void>();
  #active = false;
  #life = 0;
  #poll = 0;
  #epoch: number;
  #timer: ReturnType<typeof setTimeout> | undefined;
  #read: AbortController | undefined;
  #keys = new Map<string, string>();
  #unsubscribe: (() => void) | undefined;
  constructor(private access: AccessSession, private delay = 2000) { this.#epoch = access.snapshot().epoch; }
  snapshot = () => this.#value;
  subscribe = (listener: () => void) => { this.#listeners.add(listener); return () => { this.#listeners.delete(listener); }; };
  #current(life = this.#life) { return this.#active && life === this.#life && this.access.current(this.#epoch); }
  #set(value: Partial<Snapshot>) {
    const next = { ...this.#value, ...value };
    if (next.denied || !next.state?.evidence.some(item => item.id === next.inspectionId)) next.inspectionId = null;
    this.#value = next; this.#listeners.forEach(listener => listener());
  }
  inspect = (id: string | null) => {
    if (this.#current()) this.#set({ inspectionId: id });
  };
  start = () => {
    this.#active = true;
    this.#unsubscribe?.();
    this.#unsubscribe = this.access.subscribe(() => { if (!this.access.current(this.#epoch)) this.stop(); });
    this.refresh();
  };
  stop = () => {
    this.#active = false; this.#life++; this.#poll++; clearTimeout(this.#timer);
    this.#unsubscribe?.(); this.#unsubscribe = undefined;
    this.#read?.abort(); this.#keys.clear(); this.access.cancelPending(this.#epoch); this.access.releaseImages(this.#epoch);
    this.#set({ state: null, connection: 'loading', error: '', denied: false, busy: false });
  };
  refresh = () => {
    if (!this.#current()) return;
    clearTimeout(this.#timer); this.#read?.abort();
    const generation = ++this.#poll;
    this.#set({ error: '' });
    void this.#load(generation, 0, 0);
  };
  async #load(generation: number, failures: number, attempts: number) {
    if (!this.#current() || generation !== this.#poll) return;
    const controller = new AbortController(); this.#read = controller;
    const valid = () => this.#current() && generation === this.#poll && !controller.signal.aborted;
    try {
      const state = await this.access.state(controller.signal);
      if (!valid()) return;
      this.#set({ state, connection: 'online', denied: false }); failures = 0;
    } catch (failure) {
      if (!valid()) return;
      failures++;
      if (failure instanceof APIError && failure.code === 'access_denied') {
        this.access.releaseImages(); this.#set({ state: null, connection: 'paused', denied: true, error: failure.message }); return;
      }
      this.#set({ connection: 'paused', error: 'State could not be refreshed. Displayed data may be stale; writes are disabled.' });
    }
    if (valid() && failures < 3 && attempts + 1 < 900) this.#timer = setTimeout(() => void this.#load(generation, failures, attempts + 1), this.delay);
    else if (valid()) this.#set({ connection: 'paused' });
  }
  mutate = async (path: string, body: object | Blob, identity: string, extra: Record<string, string> = {}, progress?: UploadProgress): Promise<boolean> => {
    const life = this.#life;
    if (!this.#current(life) || this.#value.busy) return false;
    this.#set({ busy: true, error: '' });
    if (!this.#keys.has(identity)) this.#keys.set(identity, crypto.randomUUID());
    try {
      await this.access.mutate(path, body, this.#keys.get(identity)!, extra, progress);
      if (!this.#current(life)) return false;
      if (['/api/incidents', '/api/investigations', '/api/simulation/start'].includes(path)) await this.access.refreshIdentity();
      else this.refresh();
      return true;
    } catch (failure) {
      if (this.#current(life)) {
        this.#set({ error: failure instanceof Error && failure.name !== 'AbortError' ? failure.message : 'Response interrupted. State may have changed; refresh before another action.' });
        if (failure instanceof APIError && failure.code === 'access_denied') {
          clearTimeout(this.#timer); this.#poll++; this.#read?.abort(); this.access.releaseImages();
          this.#set({ state: null, connection: 'paused', denied: true });
        }
      }
      return false;
    } finally { if (this.#current(life)) this.#set({ busy: false }); }
  };
}
