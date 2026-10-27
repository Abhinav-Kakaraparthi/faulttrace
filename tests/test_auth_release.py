"""Synthetic principals, direct API allow/deny cases; no real credentials/data."""
import hashlib
import io
import json
from pathlib import Path
import secrets
import tempfile
import threading
import time
import unittest
import uuid

from fastapi.testclient import TestClient
from faulttrace.workflow.api import create_app
from faulttrace.workflow.auth import initialize_registry
from faulttrace.workflow.auth_admin import grant, issue
from faulttrace.workflow.storage import Store
from contextlib import redirect_stdout


def key():
    return str(uuid.uuid4())


class ReleaseCase(unittest.TestCase):
    def setUp(self):
        self.temp = self.enterContext(tempfile.TemporaryDirectory())
        self.root = Path(self.temp)
        self.registry = initialize_registry(self.root / 'auth.json')
        self.tokens = {}
        for pid, role, create in [('chief', 'commander', True), ('viewer', 'commander', False),
                                  ('field', 'operator', False), ('other', 'operator', False)]:
            path = self.root / (pid + '.token')
            issue(self.registry, pid, role, 1, create, path)
            self.tokens[pid] = path.read_text()
        self.data = self.root / 'data'
        self.calls = []
        self.app = create_app(self.data, self.root / 'usage.json', enabled=False,
                              send=lambda *args: self.calls.append(args),
                              profile='release', auth_registry=self.registry.path,
                              simulation_clock=lambda: time.time())
        self.client = self.enterContext(TestClient(self.app))

    def headers(self, pid='chief', **extra):
        return {'Authorization': 'Bearer ' + self.tokens[pid], **extra}

    def post(self, path, body, pid='chief', request_key=None, **headers):
        return self.client.post(path, json=body, headers=self.headers(pid,
            **{'Idempotency-Key': request_key or key(), **headers}))

    def state(self, pid='chief'):
        return self.client.get('/api/state', headers=self.headers(pid))

    def start(self):
        response = self.post('/api/investigations', {})
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()['incident_id']

    def task(self, incident, asset='F-17'):
        # Test-created assignment; production planner policy is never bypassed by API.
        tid = key()
        with self.app.state.workflow.store.connection(write=True) as db:
            db.execute('INSERT INTO tasks(id,incident_id,revision,status,created_at,asset_id,capability) '
                       "VALUES(?,?,1,'awaiting',?,?,?)", (tid, incident, 'synthetic test', asset,
                        'READ_LOCAL_DP' if asset == 'F-17' else 'OBSERVE_POSITION'))
        return tid


class AuthenticationTests(ReleaseCase):
    def test_missing_invalid_expired_revoked_and_forged_roles(self):
        for headers in ({}, {'X-FaultTrace-Local': '1', 'X-Role': 'commander'},
                        {'Authorization': 'Bearer ' + secrets.token_urlsafe(32)},
                        {'Cookie': 'Authorization=' + self.tokens['chief']}):
            response = self.client.get('/api/state?role=commander', headers=headers)
            self.assertEqual(response.status_code, 401)
            self.assertEqual(response.json(), {'error': 'authentication_required'})
            self.assertEqual(response.headers['cache-control'], 'no-store')
        for field, value in [('expires', time.time() - 1), ('revoked', True)]:
            with self.registry.edit() as registry:
                registry['principals']['chief'][field] = value
            self.assertEqual(self.state().status_code, 401)
        self.assertEqual(self.post('/api/investigations', {}, 'field', **{'X-Role': 'commander'}).status_code, 403)
        self.assertEqual(self.calls, [])

    def test_identity_create_permission_grants_and_live_revocation(self):
        self.assertEqual(self.post('/api/investigations', {}, 'viewer').json(), {'error': 'access_denied'})
        incident = self.start()
        identity = self.client.get('/api/identity', headers=self.headers()).json()
        self.assertEqual(identity, {'profile': 'release', 'principal_id': 'chief', 'role': 'commander',
            'capabilities': {'create_incident': True}, 'incident_ids': [incident]})
        self.assertEqual(self.state('field').status_code, 403)
        grant(self.registry, 'field', incident, assign=True)
        response = self.state('field')
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.json()['journey']['samples'])
        self.assertNotIn('private_outcome', response.text)
        with self.registry.edit() as registry:
            registry['principals']['field']['revoked'] = True
        self.assertEqual(self.state('field').status_code, 401)

    def test_release_configuration_fails_before_workflow_creation(self):
        for path in (None, self.root / 'missing.json'):
            directory = self.root / key()
            with self.assertRaises(ValueError):
                create_app(directory, profile='release', auth_registry=path)
            self.assertFalse(directory.exists())
        self.registry.path.write_text('{"version":1}')
        self.assertEqual(self.state().status_code, 401)

    def test_no_cookie_auth_or_ambient_browser_authority(self):
        self.assertEqual(self.client.post('/api/investigations', json={},
            headers={'Origin': 'http://127.0.0.1:5173', 'X-FaultTrace-Local': '1'}).status_code, 401)
        response = self.post('/api/investigations', {}, Origin='https://evil.invalid')
        self.assertEqual(response.status_code, 403)
        self.assertNotIn('set-cookie', response.headers)
        self.assertIsNone(self.state().json()['incident'])
        self.assertEqual(self.client.options('/api/state', headers=self.headers()).status_code, 403)

    def test_registry_only_contains_hashes(self):
        text = self.registry.path.read_text()
        for token in self.tokens.values():
            self.assertNotIn(token, text)
            self.assertIn(hashlib.sha256(token.encode()).hexdigest(), text)

    def test_audit_attributes_principal_without_credentials(self):
        self.start()
        self.post('/api/planning', {'revision': 1}, 'field')
        with self.app.state.workflow.store.connection() as db:
            rows = [dict(r) for r in db.execute('SELECT * FROM access_audit')]
        self.assertTrue(any(r['principal'] == 'chief' and r['status'] == 200 for r in rows))
        self.assertTrue(any(r['principal'] == 'field' and r['status'] == 403 for r in rows))
        for token in self.tokens.values():
            self.assertNotIn(token, json.dumps(rows))

    def test_concurrent_creators_do_not_both_gain_singleton_incident(self):
        delivery = self.root / 'second.token'
        issue(self.registry, 'second', 'commander', 1, True, delivery)
        self.tokens['second'] = delivery.read_text()
        original = self.app.state.access.authorize
        barrier = threading.Barrier(2)

        async def simultaneous(request, principal):
            await original(request, principal)
            if request.url.path == '/api/incidents':
                barrier.wait(timeout=5)
        self.app.state.access.authorize = simultaneous
        responses = []
        threads = [threading.Thread(target=lambda p=pid: responses.append(
            TestClient(self.app).post('/api/incidents', json={},
                headers=self.headers(p, **{'Idempotency-Key': key()})))) for pid in ('chief', 'second')]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=10)
        self.assertEqual(sorted(r.status_code for r in responses), [200, 403])
        grants = self.registry.read()['principals']
        self.assertEqual(sum(bool(grants[p]['incidents']) for p in ('chief', 'second')), 1)


class AdministratorTests(unittest.TestCase):
    def test_cli_issues_grants_revokes_without_printing_token(self):
        from faulttrace.workflow.auth_admin import main
        from faulttrace.workflow.auth import Registry
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory(dir=root / '.local') as temp:
            registry, delivery = Path(temp) / 'registry.json', Path(temp) / 'delivery.token'
            base = ['--registry', str(registry)]
            output = io.StringIO()
            with redirect_stdout(output):
                self.assertEqual(main(base + ['init']), 0)
                self.assertEqual(main(base + ['issue', '--principal', 'synthetic', '--role', 'operator',
                    '--hours', '1', '--token-file', str(delivery)]), 0)
                incident = key()
                self.assertEqual(main(base + ['assign-operator', '--principal', 'synthetic', '--incident', incident]), 0)
                self.assertEqual(Registry(registry).authenticate('Bearer ' + delivery.read_text())['incidents'], [incident])
                self.assertEqual(main(base + ['revoke', '--principal', 'synthetic']), 0)
            with self.assertRaises(Exception):
                Registry(registry).authenticate('Bearer ' + delivery.read_text())
            self.assertNotIn(delivery.read_text(), output.getvalue())
