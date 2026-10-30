import { APIError, type ServerState } from './api';
import type { AccessSession } from './access';
import type { UploadProgress } from './photoUpload';
import type { SubmitPhoto } from './photoSubmission';

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
  // One explicit UI action authorizes this upload and, optionally, ONE analysis.
  // Never infer the evidence ID from array order or replay an interrupted request.
  submitPhoto: SubmitPhoto = async (task, blob, identity, analyze, progress) => {
    const life = this.#life, before = this.#value.state;
    if (!this.#current(life) || this.#value.busy || this.#value.connection !== 'online'
      || !before?.incident || before.task?.id !== task.id || before.task.revision !== task.revision
      || !['awaiting', 'needs_evidence'].includes(task.status)) return 'unconfirmed';
    this.#set({ busy: true, error: '' });
    clearTimeout(this.#timer); this.#read?.abort(); this.#poll++;
    let stored = false, error = '';
    const key = (name: string) => {
      if (!this.#keys.has(name)) this.#keys.set(name, crypto.randomUUID());
      return this.#keys.get(name)!;
    };
    try {
      const response = await this.access.mutate(`/api/tasks/${task.id}/images`, blob,
        key(`photo-${task.id}-${task.revision}-${identity}`),
        { 'X-Task-Revision': String(task.revision), 'X-Evidence-Purpose': 'reference-photo' }, progress);
      if (!this.#current(life)) return 'unconfirmed';
      const id = response?.evidence_id;
      if (typeof id !== 'string' || !/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/.test(id)) throw new Error('Upload response was not confirmed. Refresh before another submission.');
      stored = true;
      const controller = new AbortController(); this.#read = controller;
      const state = await this.access.state(controller.signal);
      if (!this.#current(life)) return 'unconfirmed';
      this.#set({ state, connection: 'online', denied: false });
      if (!analyze) return 'stored';
      const evidence = state.evidence.find(item => item.id === id);
      const latest = state.evidence.filter(item => item.task_id === task.id && item.kind === 'image').at(-1);
      if (state.incident?.id !== before.incident?.id || state.incident?.revision !== before.incident.revision + 1 || state.task?.id !== task.id
        || state.task.revision !== task.revision + 1 || !['awaiting', 'needs_evidence'].includes(state.task.status)
        || evidence?.task_id !== task.id || evidence.status !== 'collected' || evidence.analysis
        || latest?.id !== id || !state.inference_enabled || state.photo_analysis?.contract !== 'photo-observation-v1') {
        throw new Error('Photograph stored. Analysis stopped because the task, evidence or inference availability changed. Review the current record.');
      }
      await this.access.mutate(`/api/evidence/${id}/analyze-photo`, { revision: state.task.revision },
        key(`photo-analysis-${id}-${state.task.revision}`));
      return this.#current(life) ? 'analysis_requested' : 'unconfirmed';
    } catch (failure) {
      if (this.#current(life)) {
        error = failure instanceof Error ? failure.message : 'Submission interrupted; refresh before another action.';
        this.#set({ error });
        if (failure instanceof APIError && failure.code === 'access_denied') {
          this.access.releaseImages(); this.#set({ state: null, connection: 'paused', denied: true });
        }
      }
      return stored ? 'stored_analysis_stopped' : 'unconfirmed';
    } finally {
      if (this.#current(life)) { this.#set({ busy: false }); if (!this.#value.denied) this.refresh(); if (error) this.#set({ error }); }
    }
  };
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
