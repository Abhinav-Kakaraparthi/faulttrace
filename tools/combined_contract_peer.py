"""Private stdio ASGI test peer. Fresh synthetic records; never a running API."""
import base64
from contextlib import ExitStack
import json
import os
from pathlib import Path
import sys
import tempfile
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.pop('NEBIUS_API_KEY', None)
os.environ['FAULTTRACE_ALLOW_INFERENCE'] = '0'
from tools.run_offline_tests import network_guard
BLOCKED = []
sys.addaudithook(network_guard(BLOCKED))
from fastapi.testclient import TestClient
from faulttrace.workflow.api import create_app
from faulttrace.workflow.auth import initialize_registry
from faulttrace.workflow.auth_admin import grant, issue


def main():
    with ExitStack() as stack:
        root = Path(stack.enter_context(tempfile.TemporaryDirectory()))
        registry = initialize_registry(root / 'registry.json')
        tokens = {}
        for principal, role in [('chief', 'commander'), ('field', 'operator')]:
            delivery = root / (principal + '.delivery')
            issue(registry, principal, role, 1, role == 'commander', delivery)
            tokens[principal] = delivery.read_text()
        calls = []
        def forbidden(*args):
            calls.append(1)
            raise AssertionError('provider_contact_forbidden')
        app = create_app(root / 'data', root / 'usage.json', enabled=False,
                         send=forbidden, key_source=lambda: None,
                         profile='release', auth_registry=registry.path)
        client = stack.enter_context(TestClient(app))
        for line in sys.stdin:
            message = json.loads(line)
            action = message['action']
            try:
                if action == 'identities':
                    result = tokens  # Private pipe only; the parent never logs this.
                elif action == 'assign':
                    incident = message['incident']
                    grant(registry, 'field', incident, assign=True)
                    task = str(uuid.uuid4())
                    with app.state.workflow.store.connection(write=True) as db:
                        db.execute('''INSERT INTO tasks(id,incident_id,revision,status,created_at,
                            asset_id,capability,creation_source,explanation)
                            VALUES(?,?,1,'awaiting','offline setup','F-17','READ_LOCAL_DP',
                            'TEST-CREATED / no model request','Offline contract-test assignment')''',
                                   (task, incident))
                    result = {'task_id': task}
                elif action == 'grant':
                    if message['allow']:
                        grant(registry, 'field', message['incident'])
                    else:
                        with registry.edit() as value:
                            value['principals']['field']['incidents'] = []
                            value['operators'].pop(message['incident'], None)
                    result = {'ok': True}
                elif action == 'request':
                    response = client.request(message['method'], message['path'],
                        headers=message['headers'], content=base64.b64decode(message['body']))
                    result = {'status': response.status_code, 'headers': dict(response.headers),
                              'body': base64.b64encode(response.content).decode('ascii')}
                elif action == 'summary':
                    with app.state.workflow.store.connection() as db:
                        result = {table: db.execute('SELECT COUNT(*) FROM ' + table).fetchone()[0]
                                  for table in ('incidents', 'tasks', 'planning', 'analyses')}
                    result.update(provider_calls=len(calls), forbidden_network=len(BLOCKED))
                elif action == 'close':
                    return
                else:
                    raise ValueError('unknown_test_action')
                print(json.dumps({'id': message['id'], 'result': result}), flush=True)
            except Exception:
                print(json.dumps({'id': message['id'], 'error': 'contract_peer_failed'}), flush=True)
        if BLOCKED or calls:
            raise RuntimeError('offline_boundary_failed')


if __name__ == '__main__':
    main()
