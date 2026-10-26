import { useEffect, useId, useRef, useState } from 'react';
import { localPhotoURL, photoDimensionsError, photoFileError, type UploadProgress } from './photoUpload';
import './photos.css';

export function PhotoDraft({ url, busy, progress, ready, failed, disabled = false, onReplace, onCancel, onSubmit, onLoad, onError }: {
  url: string; busy: boolean; disabled?: boolean; progress: number | null; ready: boolean; failed: boolean;
  onReplace: () => void; onCancel: () => void; onSubmit: () => void;
  onLoad?: React.ReactEventHandler<HTMLImageElement>; onError?: React.ReactEventHandler<HTMLImageElement>;
}) {
  return <section className="photo-draft" aria-label="Unsubmitted photograph preview" aria-busy={busy}>
    <h4>Selected photograph / not submitted</h4>
    <img className="photo-preview" src={url} alt="Selected local photograph; assignment and instrument identity have not been verified" onLoad={onLoad} onError={onError} />
    <p>Local preview only · nothing submitted yet.</p>
    <div className="photo-actions"><button type="button" className="button secondary" disabled={busy || disabled} onClick={onReplace}>Replace photograph</button><button type="button" className="button quiet" disabled={busy} onClick={onCancel}>Cancel selection</button><button type="button" className="button primary" disabled={busy || disabled || !ready || failed} onClick={onSubmit}>Submit image / collection only</button></div>
    {busy && <div role="status" className="photo-transfer"><progress max="100" value={progress ?? undefined} aria-label="Photograph upload progress" /><span>{progress === null ? 'Uploading; transfer size unavailable.' : progress === 100 ? 'Transfer complete; waiting for server validation and storage.' : `Uploading ${progress}%`}</span></div>}
  </section>;
}

export function PhotoCapture({ asset, disabled, supported, upload }: { asset: string; disabled: boolean; supported: boolean;
  upload: (blob: Blob, identity: string, progress: UploadProgress) => Promise<boolean>;
}) {
  const [file, setFile] = useState<File | null>(null);
  const [url, setURL] = useState('');
  const [error, setError] = useState('');
  const [ready, setReady] = useState(false);
  const [busy, setBusy] = useState(false);
  const [progress, setProgress] = useState<number | null>(null);
  const [message, setMessage] = useState('');
  const files = useRef<HTMLInputElement>(null), camera = useRef<HTMLInputElement>(null);
  const identity = useRef('');
  const guidanceId = useId();
  useEffect(() => {
    if (!file) { setURL(''); return; }
    const preview = localPhotoURL(file); setURL(preview.url);
    return preview.release;
  }, [file]);
  function select(next?: File) {
    setError(''); setMessage(''); setReady(false);
    setFile(null); setURL('');
    if (!next) return;
    const invalid = photoFileError(next);
    if (invalid) { setError(invalid); return; }
    identity.current = crypto.randomUUID(); setFile(next);
  }
  function cancel() { select(); if (files.current) files.current.value = ''; if (camera.current) camera.current.value = ''; }
  async function submit() {
    if (!file || !ready || busy || disabled || !supported) return;
    setBusy(true); setProgress(0); setError('');
    try {
      const saved = await upload(file, identity.current, setProgress);
      if (saved) { cancel(); setMessage('Photograph stored. No analysis was requested; observation analysis is a separate explicit action.'); }
      else setError('Photo submission was not confirmed. Review the server error and refresh state before resubmitting; the server may already have stored it.');
    } catch { setError('Photo submission interrupted. Refresh server state before another action.'); }
    finally { setBusy(false); }
  }
  const unavailable = disabled || busy || !supported;
  return <section className="photo-capture" aria-label={`${asset} photographic evidence`}>
    <h3>Add a photograph</h3><p>Include the instrument and visible tag. If the tag differs from {asset}, report wrong equipment. Upload collects evidence only; no analysis runs.</p>
    {!supported && <p className="notice">Photo collection requires the updated backend. The existing server has been left untouched; these controls stay disabled until it advertises collection support.</p>}
    <div className="photo-pickers"><label>Take a photograph<input ref={camera} type="file" accept="image/png,image/jpeg" capture="environment" aria-describedby={guidanceId} disabled={unavailable} onChange={e => select(e.target.files?.[0])} /></label><label>Choose a photograph from files<input ref={files} type="file" accept="image/png,image/jpeg" aria-describedby={guidanceId} disabled={unavailable} onChange={e => select(e.target.files?.[0])} /></label></div>
    {url && <PhotoDraft url={url} disabled={disabled || !supported} busy={busy} progress={progress} ready={ready && !disabled && supported} failed={!!error} onReplace={() => { if (files.current) { files.current.value = ''; files.current.click(); } }} onCancel={cancel} onSubmit={() => void submit()}
      onLoad={e => { const invalid = photoDimensionsError(e.currentTarget.naturalWidth, e.currentTarget.naturalHeight); setReady(!invalid); if (invalid) setError(invalid); }}
      onError={() => { setReady(false); setError('The selected image cannot be previewed. Replace it with a valid PNG or JPEG; nothing has been submitted.'); }} />}
    {error && <p className="form-error" role="alert">{error}</p>}{message && <p role="status">{message}</p>}
    <details id={guidanceId} className="photo-guidance"><summary>Photo requirements &amp; evidence limits</summary><p>PNG/JPEG, at most 2 MiB; 16 to 2048 pixels per side and at most 1,048,576 pixels. Prepare a smaller copy if needed. Camera support varies; file selection is always offered. The server strips metadata after submission.</p><p>Assignment does not identify the equipment in your photograph. An ordinary pressure gauge does not establish differential pressure. A valve handle image does not prove internal valve condition. NVIDIA analysis is separate and explicit; no photograph authorizes correction or recovery.</p></details>
  </section>;
}
