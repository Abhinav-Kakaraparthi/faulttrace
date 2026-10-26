import { useEffect, useState, type CSSProperties } from 'react';
import type { ServerEvidence } from './api';
import './photos.css';

export function EvidencePhoto({ evidence, compact = false }: { evidence: ServerEvidence; compact?: boolean }) {
  const [failed, setFailed] = useState(false);
  const [enlarged, setEnlarged] = useState(false);
  useEffect(() => { setFailed(false); setEnlarged(false); }, [evidence.id, evidence.image_url]);
  if (evidence.kind !== 'image') return null;
  const unavailable = !evidence.image_url || failed;
  const image = unavailable ? <p className="notice" role="status">Stored image unavailable</p>
    : <img src={evidence.image_url!} alt={compact ? `Stored image thumbnail for assigned ${evidence.asset_id}; identity unverified` : 'Actual stored submitted image; depicted asset identity is not verified'} loading={compact ? 'lazy' : 'eager'} onError={() => setFailed(true)} />;
  return <figure className={compact ? 'evidence-photo-thumb' : 'evidence-photo'}>
    {compact ? image : <>
      <div className="image-view-tools"><button className="button secondary" type="button" disabled={unavailable} aria-pressed={enlarged} onClick={() => setEnlarged(value => !value)}>{enlarged ? 'Fit photograph' : 'Enlarge photograph'}</button><span>Full image · no crop</span></div>
      <div className={`inspection-image-frame ${enlarged ? 'is-enlarged' : ''}`} role="region" aria-label="Full evidence photograph; scroll to inspect when enlarged" tabIndex={0} style={{ '--photo-native-width': `${evidence.width ?? 960}px` } as CSSProperties}>{image}</div>
      {!unavailable && <figcaption>{enlarged ? 'Enlarged view: focus the image region and use arrow keys or scroll to pan.' : 'Fit view: the entire photograph is visible. Enlarge to inspect details.'}</figcaption>}
    </>}
  </figure>;
}
