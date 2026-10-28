"""Deterministic creation races with synthetic identities and isolated stores."""
from concurrent.futures import ThreadPoolExecutor
import threading
import time

from fastapi.testclient import TestClient

from faulttrace.workflow.auth_admin import issue
from test_auth_release import ReleaseCase, key

STARTS = ('/api/incidents', '/api/investigations', '/api/simulation/start')


class CreationReplayTests(ReleaseCase):
    def assert_single_incident(self, incident, creator='chief'):
        with self.app.state.workflow.store.connection() as db:
            self.assertEqual([r['id'] for r in db.execute('SELECT id FROM incidents')], [incident])
            self.assertEqual(db.execute('SELECT COUNT(*) FROM operations').fetchone()[0], 1)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM events WHERE kind IN "
                "('task_investigation_started','synthetic_journey_started','simulated_incident_started')").fetchone()[0], 1)
        registry = self.registry.read()['principals']
        self.assertEqual(registry[creator]['incidents'], [incident])
        self.assertTrue(all(not p['incidents'] for pid, p in registry.items() if pid != creator))
        self.assertEqual(self.state(creator).status_code, 200)
        self.assertEqual(self.calls, [])

    def race(self, path, principals, request_key):
        original = self.app.state.access.authorize
        barrier = threading.Barrier(len(principals))

        async def admitted_together(request, principal):
            await original(request, principal)
            if request.url.path == path:
                barrier.wait(timeout=10)
        self.app.state.access.authorize = admitted_together

        def post(pid):
            return pid, TestClient(self.app).post(path, json={},
                headers=self.headers(pid, **{'Idempotency-Key': request_key}))
        try:
            with ThreadPoolExecutor(max_workers=len(principals)) as workers:
                futures = [workers.submit(post, pid) for pid in principals]
                return [future.result(timeout=20) for future in futures]
        finally:
            self.app.state.access.authorize = original

    def test_same_creator_concurrent_investigation_replay(self):
        request_key = key()
        responses = [response for _, response in self.race('/api/investigations', ['chief', 'chief'], request_key)]
        self.assertEqual([r.status_code for r in responses], [200, 200])
        self.assertEqual(responses[0].json(), responses[1].json())
        self.assert_single_incident(responses[0].json()['incident_id'])

    def test_same_creator_concurrent_legacy_start_replay(self):
        responses = [response for _, response in self.race('/api/incidents', ['chief', 'chief'], key())]
        self.assertEqual([r.status_code for r in responses], [200, 200])
        self.assertEqual(responses[0].json(), responses[1].json())
        self.assert_single_incident(responses[0].json()['incident_id'])

    def test_same_creator_concurrent_simulation_start_replay(self):
        responses = [response for _, response in self.race('/api/simulation/start', ['chief', 'chief'], key())]
        self.assertEqual([r.status_code for r in responses], [200, 200])
        self.assertEqual(responses[0].json(), responses[1].json())
        self.assert_single_incident(responses[0].json()['incident_id'])

    def test_grant_created_between_authentication_and_admission_is_reconciled(self):
        original = self.app.state.access.authorize
        entered, resume = threading.Event(), threading.Event()
        request_key = key()

        async def pause_before_admission(request, principal):
            if request.headers.get('x-test-pause') == '1':
                entered.set()
                if not resume.wait(10):
                    raise AssertionError('test_admission_timeout')
            await original(request, principal)
        self.app.state.access.authorize = pause_before_admission
        try:
            with ThreadPoolExecutor(max_workers=1) as worker:
                pending = worker.submit(lambda: TestClient(self.app).post('/api/investigations', json={},
                    headers=self.headers(**{'Idempotency-Key': request_key, 'X-Test-Pause': '1'})))
                try:
                    self.assertTrue(entered.wait(10))
                    first = self.post('/api/investigations', {}, request_key=request_key)
                    self.assertEqual(first.status_code, 200)
                finally:
                    resume.set()
                replay = pending.result(timeout=20)
            self.assertEqual(replay.status_code, 200, replay.text)
            self.assertEqual(replay.json(), first.json())
            self.assert_single_incident(first.json()['incident_id'])
        finally:
            resume.set()
            self.app.state.access.authorize = original

    def test_different_creator_cannot_acquire_or_replay_same_creation_key(self):
        delivery = self.root / 'second.token'
        issue(self.registry, 'second', 'commander', 1, True, delivery)
        self.tokens['second'] = delivery.read_text()
        request_key = key()
        results = self.race('/api/investigations', ['chief', 'second'], request_key)
        self.assertEqual(sorted(r.status_code for _, r in results), [200, 403])
        creator, accepted = next((p, r) for p, r in results if r.status_code == 200)
        loser, denied = next((p, r) for p, r in results if r.status_code == 403)
        self.assertEqual(denied.json(), {'error': 'access_denied'})
        self.assert_single_incident(accepted.json()['incident_id'], creator)
        self.assertEqual(self.post('/api/investigations', {}, loser, request_key).json(), {'error': 'access_denied'})
        self.assertEqual(self.state(loser).status_code, 403)

    def revoke_while_admitted(self, change, expected_status):
        request_key = key()
        incident = self.post('/api/investigations', {}, request_key=request_key).json()['incident_id']
        original = self.app.state.access.authorize
        entered, resume = threading.Event(), threading.Event()

        async def paused(request, principal):
            await original(request, principal)
            if request.url.path == '/api/investigations':
                entered.set()
                if not resume.wait(10):
                    raise AssertionError('test_admission_timeout')
        self.app.state.access.authorize = paused
        try:
            with ThreadPoolExecutor(max_workers=1) as worker:
                pending = worker.submit(lambda: TestClient(self.app).post('/api/investigations', json={},
                    headers=self.headers(**{'Idempotency-Key': request_key})))
                try:
                    self.assertTrue(entered.wait(10))
                    with self.registry.edit() as registry:
                        registry['principals']['chief'].update(change)
                finally:
                    resume.set()
                response = pending.result(timeout=20)
            error = 'authentication_required' if expected_status == 401 else 'access_denied'
            self.assertEqual(response.status_code, expected_status, response.text)
            self.assertEqual(response.json(), {'error': error})
        finally:
            resume.set()
            self.app.state.access.authorize = original
        subsequent = self.post('/api/investigations', {}, request_key=request_key)
        self.assertEqual(subsequent.status_code, expected_status)
        self.assertEqual(subsequent.json(), {'error': error})
        with self.app.state.workflow.store.connection() as db:
            self.assertEqual([r['id'] for r in db.execute('SELECT id FROM incidents')], [incident])
            self.assertEqual(db.execute('SELECT COUNT(*) FROM operations').fetchone()[0], 1)
        for field, value in change.items():
            self.assertEqual(self.registry.read()['principals']['chief'][field], value)

    def test_removed_incident_grant_denies_admitted_and_later_replays(self):
        self.revoke_while_admitted({'incidents': []}, 403)

    def test_expired_identity_denies_admitted_and_later_replays(self):
        self.revoke_while_admitted({'expires': time.time() - 1}, 401)

    def test_revoked_identity_denies_admitted_and_later_replays(self):
        self.revoke_while_admitted({'revoked': True}, 401)

    def test_removed_create_permission_denies_admitted_and_later_replays(self):
        self.revoke_while_admitted({'create': False}, 403)

    def test_conflicting_payload_and_operation_keys_remain_rejected(self):
        request_key = key()
        created = self.post('/api/investigations', {}, request_key=request_key)
        self.assertEqual(created.status_code, 200)
        self.assertEqual(self.post('/api/investigations', {}, request_key=request_key).json(), created.json())
        self.assertEqual(self.post('/api/investigations', {'extra': True}, request_key=request_key).json(), {'error': 'invalid_request'})
        for path in ('/api/incidents', '/api/simulation/start'):
            result = self.post(path, {}, request_key=request_key)
            self.assertEqual(result.status_code, 409)
            self.assertEqual(result.json(), {'error': 'idempotency_conflict'})
        state = self.state().json()
        revision = state['incident']['revision']
        step_key = key()
        first = self.post('/api/simulation/advance', {'revision': revision}, request_key=step_key)
        self.assertEqual(first.status_code, 200)
        self.assertEqual(self.post('/api/simulation/advance', {'revision': revision}, request_key=step_key).json(), first.json())
        conflict = self.post('/api/simulation/advance', {'revision': revision + 1}, request_key=step_key)
        self.assertEqual(conflict.status_code, 409)
        self.assertEqual(conflict.json(), {'error': 'idempotency_conflict'})
