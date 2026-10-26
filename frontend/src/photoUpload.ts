export type UploadProgress = (percent: number | null) => void;
export const MAX_PHOTO_BYTES = 2 * 1024 * 1024;

export function photoFileError(file: Pick<File, 'type' | 'size'>): string | null {
  if (!['image/png', 'image/jpeg'].includes(file.type)) return 'Choose a PNG or JPEG photograph. HEIC and other formats are not supported; ordinary file selection is also available.';
  if (!file.size || file.size > MAX_PHOTO_BYTES) return 'Choose a nonempty photograph no larger than 2 MiB.';
  return null;
}
export function photoDimensionsError(width: number, height: number): string | null {
  return width < 16 || height < 16 || width > 2048 || height > 2048 || width * height > 1048576
    ? 'Prepare a copy 16 to 2048 pixels per side and no more than 1,048,576 total pixels. The server enforces the same limits.' : null;
}

// The object URL is local-only; replacing, cancelling or unmounting must release it.
export function localPhotoURL(blob: Blob, urls = URL): { url: string; release: () => void } {
  const url = urls.createObjectURL(blob);
  let released = false;
  return { url, release: () => { if (!released) { urls.revokeObjectURL(url); released = true; } } };
}

export function uploadBlob(path: string, blob: Blob, headers: Record<string, string>, signal: AbortSignal,
  progress: UploadProgress, factory = () => new XMLHttpRequest()): Promise<Response> {
  return new Promise((resolve, reject) => {
    let xhr: XMLHttpRequest;
    try { xhr = factory(); }
    catch { reject(new Error('Upload could not start. Refresh server state; no automatic retry.')); return; }
    let done = false;
    const abortError = () => new DOMException('Upload interrupted. Refresh server state before another action.', 'AbortError');
    const finish = (failure?: Error, response?: Response) => {
      if (done) return;
      done = true; signal.removeEventListener('abort', abort); xhr.upload.onprogress = null;
      if (failure) reject(failure); else resolve(response!);
    };
    const abort = () => { xhr.abort(); finish(abortError()); };
    if (signal.aborted) { finish(abortError()); return; }
    signal.addEventListener('abort', abort, { once: true });
    xhr.upload.onprogress = event => progress(event.lengthComputable && event.total > 0 ? Math.min(100, Math.floor(event.loaded / event.total * 100)) : null);
    xhr.onload = () => {
      if (xhr.status < 100) { finish(new Error('Upload connection failed. Refresh server state; no automatic retry.')); return; }
      try { finish(undefined, new Response(xhr.responseText, { status: xhr.status })); }
      catch { finish(new Error('Upload response could not be read. Refresh server state before another action.')); }
    };
    xhr.onerror = () => finish(new Error('Upload connection failed. Refresh server state; no automatic retry.'));
    xhr.ontimeout = () => finish(new Error('Upload timed out. The server may have stored it; refresh before another action.'));
    xhr.onabort = () => finish(abortError());
    try {
      xhr.open('POST', path); xhr.timeout = 15000;
      for (const [name, value] of Object.entries(headers)) xhr.setRequestHeader(name, value);
      progress(0); xhr.send(blob);
    } catch { finish(new Error('Upload could not start. No automatic retry; refresh server state.')); }
  });
}
