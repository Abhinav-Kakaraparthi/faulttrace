import { defineConfig } from 'vite';

export default defineConfig({
  server: {
    host: '127.0.0.1', port: 5173, strictPort: true,
    fs: { strict: true, deny: ['.env', '.env.*', '*.{crt,pem}', '**/.git/**', '**/.local/**', '**/.venv/**'] },
    proxy: { '/api': { target: 'http://127.0.0.1:8765', changeOrigin: true } },
  },
});
