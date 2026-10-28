import type { UploadProgress } from './photoUpload';
import type { ServerEvidence, ServerState } from './api';

export type Mutate = (path: string, body: object | Blob, identity: string, extra?: Record<string, string>, onUploadProgress?: UploadProgress) => Promise<boolean>;
export type WorkspaceProps = {
  release?: boolean; canCreate?: boolean; creationReady?: boolean;
  state: ServerState | null; connection: 'loading' | 'online' | 'paused'; disabled: boolean;
  mutate: Mutate; inspect: (item: ServerEvidence) => void; analyze: (item: ServerEvidence) => void;
  navigate: (href: string) => void;
};
