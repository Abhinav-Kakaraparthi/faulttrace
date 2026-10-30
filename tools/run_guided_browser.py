"""Build and exercise a fresh isolated guided investigation; no external providers."""
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time
from urllib.request import urlopen
import uuid

ROOT = Path(__file__).resolve().parents[1]


def main():
    node = shutil.which('node')
    if not node:
        raise RuntimeError('existing_node_runtime_required')
    root = ROOT / '.local' / 'continuation-browser' / uuid.uuid4().hex
    root.mkdir(parents=True)
    env = dict(os.environ, VITE_FAULTTRACE_PROFILE='local', FAULTTRACE_ALLOW_INFERENCE='0',
               FAULTTRACE_LANGSMITH_TRACING='0', FAULTTRACE_TAVILY_ENABLED='0')
    for secret in ('NEBIUS_API_KEY', 'TAVILY_API_KEY', 'LANGSMITH_API_KEY'):
        env.pop(secret, None)
    subprocess.run([node, str(ROOT / 'frontend/node_modules/vite/bin/vite.js'), 'build',
                    '--outDir', str(root / 'dist')], cwd=ROOT / 'frontend', env=env, check=True)
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    (root.parent / 'current.json').write_text(json.dumps({'root': str(root), 'port': port}))
    env.update(FAULTTRACE_BROWSER_REVIEW_ROOT=str(root), FAULTTRACE_PREVIEW_ORIGIN=f'http://127.0.0.1:{port}')
    with (root / 'server.log').open('w', encoding='utf-8') as log:
        server = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'tools.connected_browser_demo:create_demo',
            '--factory', '--host', '127.0.0.1', '--port', str(port)], cwd=ROOT, env=env, stdout=log, stderr=log)
        try:
            for _ in range(100):
                if server.poll() is not None:
                    raise RuntimeError('isolated_browser_server_exited')
                try:
                    with urlopen(env['FAULTTRACE_PREVIEW_ORIGIN'] + '/healthz', timeout=1):
                        break
                except OSError:
                    time.sleep(.1)
            else:
                raise RuntimeError('isolated_browser_server_not_ready')
            subprocess.run([node, 'tests/guided-browser.mjs'], cwd=ROOT / 'frontend', env=env, check=True)
        finally:
            server.terminate()
            try:
                server.wait(timeout=10)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait()
    print('PASS: isolated guided browser evidence saved under ' + str(root))


if __name__ == '__main__':
    main()
