import type { UploadProgress } from './photoUpload';
import type { ServerEvidence, ServerState } from './api';

export type Mutate = (path: string, body: object | Blob, identity: string, extra?: Record<string, string>, onUploadProgress?: UploadProgress) => Promise<boolean>;
export type WorkspaceProps = {
  access?: import('./access').AccessSession;
  release?: boolean; canCreate?: boolean; creationReady?: boolean;
  state: ServerState | null; connection: 'loading' | 'online' | 'paused'; disabled: boolean;
  mutate: Mutate; inspect: (item: ServerEvidence) => void; analyze: (item: ServerEvidence) => void;
  submitPhoto?: import('./photoSubmission').SubmitPhoto;
  navigate: (href: string) => void;
};
