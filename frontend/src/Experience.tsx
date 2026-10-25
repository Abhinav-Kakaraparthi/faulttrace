import { useEffect, useState } from 'react';
import { SamplePreview } from './App';
import { Connected } from './Connected';
import { resolveRoute } from './routing';
import './connected.css';

export function App() {
  const [route, setRoute] = useState(() => resolveRoute(new URL(location.href)));
  function update() {
    const next = resolveRoute(new URL(location.href));
    const current = location.pathname + location.search + location.hash;
    if (next.canonical !== current) history.replaceState(null, '', next.canonical);
    setRoute(next);
  }
  function navigate(href: string) { history.pushState(null, '', href); update(); }
  useEffect(() => {
    update(); window.addEventListener('popstate', update);
    return () => window.removeEventListener('popstate', update);
  }, []);
  useEffect(() => {
    document.title = `${route.kind === 'connected' ? route.workspace === 'commander' ? 'Commander' : 'Operator' : route.kind === 'sample' ? 'Sample preview' : 'Page not found'} | FaultTrace`;
    const frame = requestAnimationFrame(() => { window.scrollTo({ top: 0 }); document.getElementById('main-content')?.focus({ preventScroll: true }); });
    return () => cancelAnimationFrame(frame);
  }, [route.canonical, route.kind]);
  const modeLink = (href: string, label: string, active: boolean) => <a href={href} aria-current={active ? 'page' : undefined} onClick={e => { if (e.button === 0 && !e.ctrlKey && !e.metaKey && !e.shiftKey && !e.altKey) { e.preventDefault(); navigate(href); } }}>{label}</a>;
  return <><nav className="mode-bar" aria-label="Experience mode"><strong>FaultTrace</strong>{modeLink('/commander', 'Server workspaces', route.kind === 'connected')}{modeLink('/?mode=sample', 'Sample preview', route.kind === 'sample')}<span>{route.kind === 'sample' ? 'Local tab only / no inference' : 'Local server / route separation is not authentication'}</span></nav>
    {route.kind === 'sample' ? <SamplePreview /> : route.kind === 'connected' ? <Connected workspace={route.workspace} navigate={navigate} /> : <main id="main-content" tabIndex={-1} className="commander"><h1>Page not found</h1><p>No workflow action was taken. Open a workspace:</p><a href="/commander">Commander</a> / <a href="/operator">Operator</a></main>}
  </>;
}
