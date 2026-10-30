import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';
import './refinement.css';
// Base/sample rules must precede the connected-workspace overrides in production.
import { App } from './Experience';

createRoot(document.getElementById('root')!).render(<StrictMode><App /></StrictMode>);
