"""Roles, persisted assignment and scoped evidence are enforced at API boundaries."""
from pathlib import Path

from fastapi.testclient import TestClient
from faulttrace.workflow.api import create_app
from faulttrace.workflow.auth_admin import grant
from test_auth_release import ReleaseCase, key


class ResourceTests(ReleaseCase):
    def test_task_role_assignment_images_and_scoped_results(self):
        incident = self.start()
        old_task = self.task(incident)  # No Operator was assigned at creation.
        grant(self.registry, 'field', incident, assign=True)
        grant(self.registry, 'other', incident)  # Grant alone does not assign tasks.
        task = self.task(incident)
        fixture = Path(__file__).resolve().parents[1] / 'fixtures/image-evidence/panel-a.png'
        path = f'/api/tasks/{task}/images'
        headers = {'X-Task-Revision': '1', 'Content-Type': 'image/png', 'X-Fixture-Id': 'panel-a', 'Idempotency-Key': key()}
        for pid in ('chief', 'other'):
            self.assertEqual(self.client.post(path, content=fixture.read_bytes(), headers=self.headers(pid, **headers)).status_code, 403)
        uploaded = self.client.post(path, content=fixture.read_bytes(), headers=self.headers('field', **headers))
        self.assertEqual(uploaded.status_code, 200, uploaded.text)
        eid = uploaded.json()['evidence_id']
        self.assertEqual(self.client.post(path, content=fixture.read_bytes(), headers=self.headers('field', **headers)).json(), uploaded.json())
        self.assertEqual(self.post(f'/api/tasks/{old_task}/reports', {'revision': 1, 'report': 'unreadable'}, 'field').status_code, 403)
        for pid in ('chief', 'field'):
            image = self.client.get(f'/api/evidence/{eid}/image', headers=self.headers(pid))
            self.assertEqual(image.status_code, 200)
            self.assertEqual(image.headers['cache-control'], 'no-store')
            # Authorized analysis reaches the existing inference-disabled gate.
            for action in ('analyze', 'analyze-photo'):
                result = self.post(f'/api/evidence/{eid}/{action}', {'revision': 2}, pid)
                self.assertEqual(result.json(), {'error': 'inference_disabled'})
        for identifier in (eid, key()):
            response = self.client.get(f'/api/evidence/{identifier}/image', headers=self.headers('other'))
            self.assertEqual(response.status_code, 403)
            self.assertEqual(response.json(), {'error': 'access_denied'})
        self.assertEqual(self.state('other').json()['evidence'], [])
        self.assertEqual([t['id'] for t in self.state('field').json()['tasks']], [task])
        self.assertEqual(len(self.state('chief').json()['tasks']), 2)
        self.assertEqual(self.calls, [])

    def test_cross_incident_grant_denial_and_commander_actions(self):
        incident = self.start()
        grant(self.registry, 'other', key(), assign=True)
        grant(self.registry, 'field', incident, assign=True)
        task = self.task(incident)
        for path in ('/api/planning', '/api/simulation/advance', '/api/simulation/approve', f'/api/tasks/{task}/reopen'):
            self.assertEqual(self.post(path, {'revision': 1}, 'field').status_code, 403)
        self.assertEqual(self.state('other').status_code, 403)
        self.assertEqual(self.post(f'/api/tasks/{task}/reports', {'revision': 1, 'report': 'cannot-access'}, 'other').status_code, 403)
        self.assertEqual(self.post('/api/simulation/execute', {'revision': 1, 'approval_id': key()}, 'chief').status_code, 403)
        self.assertEqual(self.post('/api/simulation/observe', {}, 'field').status_code, 403)

    def test_restart_retains_assignment_and_does_not_assign_old_tasks(self):
        incident = self.start()
        old = self.task(incident)
        grant(self.registry, 'field', incident, assign=True)
        assigned = self.task(incident)
        with TestClient(create_app(self.root / 'second', enabled=False, profile='release', auth_registry=self.registry.path)):
            pass
        # Reinitialize access over the same store without touching task history.
        from faulttrace.workflow.access import Access
        access = Access(self.app.state.workflow.store, self.registry)
        access.task(self.registry.authenticate('Bearer ' + self.tokens['field']), assigned)
        with self.assertRaisesRegex(Exception, 'access_denied'):
            access.task(self.registry.authenticate('Bearer ' + self.tokens['field']), old)
