export type Workspace = 'commander' | 'operator';
export type AppRoute = { kind: 'connected'; workspace: Workspace; canonical: string }
  | { kind: 'sample' | 'not-found'; canonical: string };

// Route identity is presentation only; it confers no server authorization.
export function resolveRoute(url: URL): AppRoute {
  const path = url.pathname.replace(/\/$/, '') || '/';
  if (path === '/commander' || path === '/operator' || path === '/') {
    if (path === '/' && url.searchParams.get('mode') === 'sample') {
      return { kind: 'sample', canonical: url.pathname + url.search + url.hash };
    }
    const workspace = path === '/operator' || (path === '/' && url.searchParams.get('view') === 'operator') ? 'operator' : 'commander';
    const canonical = new URL(url);
    canonical.pathname = '/' + workspace;
    canonical.searchParams.delete('mode'); canonical.searchParams.delete('view');
    return { kind: 'connected', workspace, canonical: canonical.pathname + canonical.search + canonical.hash };
  }
  return { kind: 'not-found', canonical: url.pathname + url.search + url.hash };
}
