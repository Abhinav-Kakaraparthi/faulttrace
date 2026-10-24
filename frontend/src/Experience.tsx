import { useState } from 'react';
import { SamplePreview } from './App';
import { Connected } from './Connected';
import './connected.css';

export function App() {
  const [mode, setMode] = useState<'connected' | 'sample'>(new URLSearchParams(location.search).get('mode') === 'sample' ? 'sample' : 'connected');
  function choose(next: 'connected' | 'sample') {
    setMode(next);
    const url = new URL(location.href); url.searchParams.set('mode', next); history.replaceState(null, '', url);
  }
  return <><div className="mode-bar" role="group" aria-label="Experience mode"><strong>FaultTrace</strong><button aria-pressed={mode === 'connected'} onClick={() => choose('connected')}>Server workflow</button><button aria-pressed={mode === 'sample'} onClick={() => choose('sample')}>Sample preview</button><span>{mode === 'sample' ? 'Local tab only · no inference' : 'Local server · explicit inference only'}</span></div>{mode === 'sample' ? <SamplePreview /> : <Connected />}</>;
}
