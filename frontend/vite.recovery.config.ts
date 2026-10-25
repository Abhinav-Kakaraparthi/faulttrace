import { defineConfig } from 'vite';
import base from './vite.config';

// Separate opt-in preview; does not reconfigure an existing 5173 server.
export default defineConfig({
  ...base,
  server: {
    ...base.server, host: '127.0.0.1', port: 5180, strictPort: true,
    proxy: { '/api': { target: 'http://127.0.0.1:8780', changeOrigin: true } },
  },
});
