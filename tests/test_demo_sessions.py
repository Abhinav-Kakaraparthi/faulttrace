"""Independent cookie/isolation expectations; temporary runs and zero inference."""
import asyncio
from contextlib import closing
from http.cookies import SimpleCookie
import json
from pathlib import Path
import tempfile
import sqlite3
import unittest
import uuid

import httpx
from fastapi.testclient import TestClient
from faulttrace.workflow.demo_app import create_demo_app

ORIGIN = 'http://127.0.0.1:5211'
COOKIE = 'faulttrace_demo_local'


class DemoTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.clock = [1000.0]
        self.app = create_demo_app(self.root, ORIGIN, local_http=True, clock=lambda: self.clock[0], ttl=120)
        self.client = self.enterContext(TestClient(self.app, base_url=ORIGIN))

    def request(self, method, path, visitor=None, body=None, key=None, role='commander', **overrides):
        self.client.cookies.clear()
        headers = {'Origin': ORIGIN, 'X-FaultTrace-Demo': '1', 'X-FaultTrace-Workspace': role}
        if visitor:
            headers.update({'Cookie': COOKIE + '=' + visitor['cookie'],
                'X-CSRF-Token': visitor['csrf_token'], 'X-FaultTrace-Demo-Run': visitor['active_run'] or ''})
        if method == 'POST':
            headers['Idempotency-Key'] = key or str(uuid.uuid4())
        for name, value in overrides.items():
            if value is None:
                headers.pop(name, None)
            else:
                headers[name] = value
        return self.client.request(method, path, headers=headers, json=body if method == 'POST' else None)

    def bootstrap(self):
        response = self.request('GET', '/api/demo/session')
        self.assertEqual(response.status_code, 200, response.text)
        cookies = SimpleCookie(response.headers['set-cookie'])
        value = dict(response.json(), cookie=cookies[COOKIE].value)
        self.assertTrue(value['cookie'] not in response.text, 'cookie must not appear in JSON')
        self.assertIn('HttpOnly', response.headers['set-cookie'])
        self.assertIn('SameSite=strict', response.headers['set-cookie'])
        self.assertIn('Path=/api', response.headers['set-cookie'])
        self.assertNotIn('Domain=', response.headers['set-cookie'])
        return value

    def start(self):
        visitor = self.bootstrap()
        response = self.request('POST', '/api/demo/start', visitor, {})
        self.assertEqual(response.status_code, 200, response.text)
        return dict(response.json(), cookie=visitor['cookie'])

    def state(self, visitor, role='commander'):
        response = self.request('GET', '/api/state', visitor, role=role)
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def upload(self, visitor):
        state = self.state(visitor, 'operator')
        self.client.cookies.clear()
        image = Path(__file__).resolve().parents[1] / 'fixtures/image-evidence/panel-a.png'
        return self.client.post('/api/tasks/' + state['task']['id'] + '/images', content=image.read_bytes(), headers={
            'Origin': ORIGIN, 'X-FaultTrace-Demo': '1', 'X-FaultTrace-Workspace': 'operator',
            'Cookie': COOKIE + '=' + visitor['cookie'], 'X-CSRF-Token': visitor['csrf_token'],
            'X-FaultTrace-Demo-Run': visitor['active_run'], 'Content-Type': 'image/png',
            'X-Task-Revision': str(state['task']['revision']), 'X-Evidence-Purpose': 'reference-photo',
            'Idempotency-Key': str(uuid.uuid4())})

    def test_automatic_creation_both_views_and_refresh_without_exposed_credentials(self):
        visitor = self.start()
        first = self.state(visitor)
        operator = self.state(visitor, 'operator')
        self.assertEqual(first['incident'], operator['incident'])
        self.assertEqual(first['task']['id'], operator['task']['id'])
        self.assertEqual(first['task']['asset_id'], 'F-17')
        self.assertIn('not NVIDIA-generated', first['task']['creation_source'])
        self.assertFalse(first['inference_enabled'])
        self.assertEqual(first['planning'], [])
        refreshed = self.request('GET', '/api/demo/session', visitor).json()
        self.assertEqual(refreshed['active_run'], visitor['active_run'])
        for role in ('commander', 'operator'):
            identity = self.request('GET', '/api/identity', visitor, role=role).json()
            self.assertEqual(identity['profile'], 'demo')
            self.assertEqual(identity['role'], role)
            self.assertFalse(identity['capabilities']['create_incident'])
        stored = (self.root / 'sessions.sqlite3').read_bytes()
        self.assertTrue(visitor['cookie'].encode() not in stored, 'store only cookie hashes')

    def test_origin_csrf_authorization_and_unsafe_bootstrap_fail_closed(self):
        visitor = self.start()
        for extra in ({'Origin': None}, {'Origin': 'https://evil.invalid'}, {'X-CSRF-Token': None},
                      {'X-CSRF-Token': 'wrong'}, {'Sec-Fetch-Site': 'same-site'},
                      {'Authorization': 'Bearer untrusted'}, {'X-FaultTrace-Demo': None}):
            response = self.request('POST', '/api/simulation/advance', visitor, {'revision': 2}, **extra)
            self.assertEqual(response.status_code, 403)
        for extra in ({'X-FaultTrace-Demo': None}, {'Sec-Fetch-Site': 'cross-site'}, {'Origin': 'null'}):
            self.assertEqual(self.request('GET', '/api/demo/session', **extra).status_code, 403)
        self.assertEqual(self.state(visitor)['journey']['tick'], 0)

    def test_expiry_end_and_history_retention(self):
        visitor = self.start()
        directory = self.root / 'runs' / visitor['active_run']
        self.clock[0] += 121
        response = self.request('GET', '/api/state', visitor)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {'error': 'demo_session_expired'})
        self.assertIn('Max-Age=0', response.headers['set-cookie'])
        self.assertTrue((directory / 'data/workflow.sqlite3').exists())
        newer = self.start()
        self.assertNotEqual(newer['active_run'], visitor['active_run'])
        self.assertEqual(self.request('POST', '/api/demo/end', newer, {}).status_code, 200)
        self.assertEqual(self.request('GET', '/api/state', newer).status_code, 401)

    def test_cross_session_tasks_images_results_corrections_and_csrf_denied(self):
        first, second = self.start(), self.start()
        a, b = self.state(first), self.state(second)
        self.assertNotEqual(a['incident']['id'], b['incident']['id'])
        uploaded = self.upload(second)
        self.assertEqual(uploaded.status_code, 200, uploaded.text)
        eid = uploaded.json()['evidence_id']
        analysis_id = str(uuid.uuid4())
        # An explicitly synthetic failed result in the isolated test DB, not model output.
        with closing(sqlite3.connect(self.root / 'runs' / second['active_run'] / 'data/workflow.sqlite3')) as db, db:
            db.execute("INSERT INTO analyses VALUES(?,?,'failed','offline test',NULL,NULL,'probe_failed','pending')", (analysis_id, eid))
        self.assertEqual(self.state(second)['evidence'][0]['analysis']['id'], analysis_id)
        self.assertTrue(analysis_id not in json.dumps(self.state(first)))
        self.assertEqual(self.request('GET', f'/api/evidence/{eid}/image', second).status_code, 200)
        self.assertEqual(self.request('GET', f'/api/evidence/{eid}/image', first).status_code, 403)
        self.assertEqual(self.request('POST', f"/api/tasks/{b['task']['id']}/reports", first,
            {'revision': 1, 'report': 'cannot-access'}, role='operator').status_code, 403)
        self.assertEqual(self.request('POST', '/api/simulation/execute', first,
            {'revision': 2, 'approval_id': str(uuid.uuid4())}, role='operator').status_code, 403)
        self.assertEqual(self.request('POST', '/api/simulation/advance', first,
            {'revision': 2}, **{'X-CSRF-Token': second['csrf_token']}).status_code, 403)
        self.assertTrue(eid not in json.dumps(self.state(first)))
        disabled = self.request('POST', f'/api/evidence/{eid}/analyze-photo', second, {'revision': 2})
        self.assertEqual(disabled.json(), {'error': 'inference_disabled'})
        self.assertEqual(self.state(second)['evidence'][0]['analysis']['id'], analysis_id)

    def test_start_duplicate_and_restart_stale_tab_never_retargets(self):
        visitor = self.bootstrap()
        key = str(uuid.uuid4())
        a = self.request('POST', '/api/demo/start', visitor, {}, key=key)
        b = self.request('POST', '/api/demo/start', visitor, {}, key=key)
        self.assertEqual(a.json(), b.json())
        visitor = dict(a.json(), cookie=visitor['cookie'])
        old = visitor.copy()
        key = str(uuid.uuid4())
        a = self.request('POST', '/api/demo/restart', old, {}, key=key)
        b = self.request('POST', '/api/demo/restart', old, {}, key=key)
        self.assertEqual(a.json(), b.json())
        visitor.update(a.json())
        self.assertNotEqual(visitor['active_run'], old['active_run'])
        response = self.request('POST', '/api/simulation/advance', old, {'revision': 2})
        self.assertEqual(response.json(), {'error': 'demo_session_changed'})
        self.assertEqual(self.state(visitor)['journey']['tick'], 0)
        self.assertEqual(len(list((self.root / 'runs').iterdir())), 2)

    def test_concurrent_start_same_cookie_and_key_creates_one_run(self):
        visitor = self.bootstrap()
        async def race():
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=self.app), base_url=ORIGIN) as client:
                headers = {'Origin': ORIGIN, 'X-FaultTrace-Demo': '1',
                    'Cookie': COOKIE + '=' + visitor['cookie'], 'X-CSRF-Token': visitor['csrf_token'],
                    'Idempotency-Key': str(uuid.uuid4())}
                return await asyncio.gather(*[client.post('/api/demo/start', json={}, headers=headers) for _ in range(2)])
        results = asyncio.run(race())
        self.assertEqual([r.status_code for r in results], [200,200])
        self.assertEqual(results[0].json(), results[1].json())
        self.assertEqual(len(list((self.root / 'runs').iterdir())), 1)

    def test_template_assignments_inherit_operator_and_preserve_refusal(self):
        visitor = self.start()
        state = self.state(visitor)
        self.assertEqual(self.request('POST', '/api/demo/observations', visitor,
            {'action_id': 'OBSERVE_V-08_OBSERVE_POSITION', 'revision': 2}).status_code, 409)
        task = state['task']
        self.assertEqual(self.request('POST', f"/api/tasks/{task['id']}/reports", visitor,
            {'revision': 1, 'report': 'cannot-access'}, role='operator').status_code, 200)
        revision = self.state(visitor)['incident']['revision']
        self.assertEqual(self.request('POST', '/api/demo/observations', visitor,
            {'action_id': 'OBSERVE_F-17_READ_LOCAL_DP', 'revision': revision}).status_code, 409)
        key = str(uuid.uuid4())
        body = {'action_id': 'OBSERVE_V-08_OBSERVE_POSITION', 'revision': revision}
        first = self.request('POST', '/api/demo/observations', visitor, body, key=key)
        self.assertEqual(first.status_code, 200, first.text)
        self.assertEqual(self.request('POST', '/api/demo/observations', visitor, body, key=key).json(), first.json())
        self.assertEqual(self.state(visitor, 'operator')['task']['asset_id'], 'V-08')
        self.assertEqual(self.state(visitor)['planning_remaining'], 4)

    def test_https_cookie_and_http_configuration_boundaries(self):
        with self.assertRaises(ValueError):
            create_demo_app(self.root / 'bad', 'http://public.example', local_http=True)
        secure = create_demo_app(self.root / 'secure', 'https://demo.example')
        with TestClient(secure, base_url='https://demo.example') as client:
            response = client.get('/api/demo/session', headers={'X-FaultTrace-Demo': '1'})
            self.assertIn('Secure', response.headers['set-cookie'])
            self.assertIn('__Host-faulttrace_demo', response.headers['set-cookie'])
            self.assertNotIn('Domain=', response.headers['set-cookie'])

    def test_bounded_bootstrap_and_restarts(self):
        visitor = self.start()
        for _ in range(2):
            result = self.request('POST', '/api/demo/restart', visitor, {})
            self.assertEqual(result.status_code, 200)
            visitor.update(result.json())
        self.assertEqual(self.request('POST', '/api/demo/restart', visitor, {}).status_code, 429)
        self.assertEqual(len(list((self.root / 'runs').iterdir())), 3)

    def prepare_reports(self, visitor):
        for asset in ('F-17', 'V-08'):
            state = self.state(visitor)
            if asset == 'V-08':
                response = self.request('POST', '/api/demo/observations', visitor,
                    {'action_id': 'OBSERVE_V-08_OBSERVE_POSITION', 'revision': state['incident']['revision']})
                self.assertEqual(response.status_code, 200)
                state = self.state(visitor, 'operator')
            task = state['task']
            self.assertEqual(task['asset_id'], asset)
            valve = asset == 'V-08'
            value = {'revision': state['incident']['revision'], 'task_revision': task['revision'],
                'photo_id': None, 'decision': 'independent', 'observed_asset_id': asset,
                'measurement_type': 'position' if valve else 'differential_pressure',
                'reading': None if valve else 180, 'unit': None if valve else 'kPa',
                'position': 'intermediate' if valve else None, 'independent': True}
            result = self.request('POST', f"/api/tasks/{task['id']}/observations", visitor, value, role='operator')
            self.assertEqual(result.status_code, 200, result.text)
        state = self.state(visitor)
        return state

    def test_complete_human_reports_approval_assignment_and_independent_recovery(self):
        visitor = self.start()
        state = self.prepare_reports(visitor)
        self.assertTrue(state['journey']['assessment']['eligible'])
        value = {'revision': state['incident']['revision'], 'action_id': state['journey']['action_id'], 'decision': 'approve'}
        self.assertEqual(self.request('POST', '/api/simulation/approve', visitor, value, role='operator').status_code, 403)
        approved = self.request('POST', '/api/simulation/approve', visitor, value)
        self.assertEqual(approved.status_code, 200)
        assigned = self.state(visitor, 'operator')['journey']
        self.assertEqual(assigned['approval_id'], approved.json()['approval_id'])
        body = {'revision': state['incident']['revision'], 'approval_id': assigned['approval_id']}
        self.assertEqual(self.request('POST', '/api/simulation/execute', visitor, body, role='operator').status_code, 200)
        self.assertEqual(self.state(visitor)['journey']['recovery']['status'], 'observing')
        for tick in range(5):
            state = self.state(visitor)
            self.assertEqual(self.request('POST', '/api/simulation/advance', visitor,
                {'revision': state['incident']['revision']}).status_code, 200)
            self.assertEqual(self.state(visitor)['journey']['recovery']['status'], 'verified' if tick == 4 else 'observing')
        self.assertEqual(self.state(visitor)['planning'], [])

    def test_capacity_and_persistence_across_new_app_lifespan(self):
        visitor = self.start()
        state = self.state(visitor)
        # Close only this test-created app; then reopen its synthetic session root.
        self.client.__exit__(None, None, None)
        replacement = create_demo_app(self.root, ORIGIN, local_http=True, clock=lambda: self.clock[0], ttl=120, limit=1)
        with TestClient(replacement, base_url=ORIGIN) as client:
            headers = {'Origin': ORIGIN, 'X-FaultTrace-Demo': '1', 'X-FaultTrace-Workspace': 'operator',
                'Cookie': COOKIE + '=' + visitor['cookie'], 'X-FaultTrace-Demo-Run': visitor['active_run']}
            response = client.get('/api/state', headers=headers)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['task']['id'], state['task']['id'])
            client.cookies.clear()
            self.assertEqual(client.get('/api/demo/session', headers={'X-FaultTrace-Demo': '1'}).status_code, 503)

    def test_duplicate_upload_at_limit_and_sanitized_failure(self):
        visitor = self.start()
        for _ in range(4):
            response = self.upload(visitor)
            self.assertEqual(response.status_code, 200)
        # A new upload is bounded; replay of an existing committed operation is not a new upload.
        self.assertEqual(self.upload(visitor).status_code, 429)
        replay = self.client.send(response.request)
        self.assertEqual(replay.status_code, 200)
        self.assertEqual(replay.json(), response.json())
        state = self.state(visitor, 'operator')
        self.assertEqual(len(state['evidence']), 4)
        def fail(*args):
            raise RuntimeError('PRIVATE_FAILURE_SENTINEL')
        self.app.state.sessions.get = fail
        result = self.request('GET', '/api/state', visitor)
        self.assertEqual(result.json(), {'error': 'storage_or_internal_failure'})
        self.assertTrue('PRIVATE_FAILURE_SENTINEL' not in result.text)

    def test_actual_foreign_approval_cannot_execute_another_visitors_correction(self):
        first, second = self.start(), self.start()
        ready = self.prepare_reports(second)
        approval = self.request('POST', '/api/simulation/approve', second, {
            'revision': ready['incident']['revision'], 'action_id': ready['journey']['action_id'], 'decision': 'approve'})
        self.assertEqual(approval.status_code, 200)
        result = self.request('POST', '/api/simulation/execute', first, {
            'revision': self.state(first)['incident']['revision'], 'approval_id': approval.json()['approval_id']}, role='operator')
        self.assertEqual(result.status_code, 403)
        self.assertEqual(self.state(second)['journey']['maintenance_status'], 'not_completed')
        self.assertTrue(self.state(second)['journey']['approval_current'])
