import { useEffect, useState } from 'react';
import type { ServerEvidence } from './api';
import './photos.css';

export function EvidencePhoto({ evidence, compact = false }: { evidence: ServerEvidence; compact?: boolean }) {
  const [failed, setFailed] = useState(false);
  useEffect(() => setFailed(false), [evidence.id, evidence.image_url]);
  if (evidence.kind !== 'image') return null;
  return <figure className="evidence-photo">
    {!evidence.image_url || failed ? <p className="notice">Stored image unavailable. Metadata alone does not establish what was photographed.</p>
      : <img className="photo-preview" src={evidence.image_url} alt="Actual stored submitted image; depicted asset identity is not verified" loading={compact ? 'lazy' : 'eager'} onError={() => setFailed(true)} />}
    <figcaption>{evidence.origin === 'synthetic-fixture' ? 'Committed synthetic fixture / regression evidence, not an equipment photograph.' : 'User-supplied image / source and authenticity not independently verified.'} Assigned asset: {evidence.asset_id}; photographed identity is not established by assignment.</figcaption>
  </figure>;
}
