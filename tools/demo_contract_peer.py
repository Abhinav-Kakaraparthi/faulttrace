"""Isolated cookie-demo ASGI peer for actual frontend contract verification."""
import base64
import json
import os
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.pop('NEBIUS_API_KEY', None)
os.environ['FAULTTRACE_ALLOW_INFERENCE'] = '0'
from tools.run_offline_tests import network_guard
blocked = []
sys.addaudithook(network_guard(blocked))
from fastapi.testclient import TestClient
from faulttrace.workflow.demo_app import create_demo_app


def main():
    clock = [1000.0]
    with tempfile.TemporaryDirectory() as temporary:
        app = create_demo_app(temporary, 'http://127.0.0.1:5211', local_http=True, clock=lambda: clock[0])
        with TestClient(app, base_url='http://127.0.0.1:5211') as client:
            for line in sys.stdin:
                message = json.loads(line)
                try:
                    if message['action'] == 'close':
                        return
                    if message['action'] == 'expire':
                        clock[0] += 7201
                        result = {'expired': True}
                    elif message['action'] == 'summary':
                        result = {'forbidden_external_attempts': len(blocked),
                            'runs': len(list((Path(temporary) / 'runs').glob('*'))),
                            'ledger_files': len(list(Path(temporary).glob('runs/*/usage.json')))}
                    else:
                        client.cookies.clear()  # Cookie jars belong to simulated browsers in Node.
                        response = client.request(message['method'], message['path'],
                            headers=message['headers'], content=base64.b64decode(message['body']))
                        result = {'status': response.status_code, 'headers': dict(response.headers),
                            'body': base64.b64encode(response.content).decode()}
                    print(json.dumps({'id': message['id'], 'result': result}), flush=True)
                except Exception:
                    print(json.dumps({'id': message['id'], 'error': 'demo_peer_failed'}), flush=True)


if __name__ == '__main__':
    main()
