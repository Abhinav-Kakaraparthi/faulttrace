"""Collection boundaries only: generated in-memory JPEG, fake transport, temp stores."""
from io import BytesIO
from pathlib import Path
import unittest

from PIL import Image
from test_workflow_api import WorkflowCase, key, LOCAL
from faulttrace.workflow.storage import Store


def jpeg():
    output = BytesIO()
    exif = Image.Exif()
    exif[270] = 'PRIVATE_TEST_METADATA'
    Image.new('RGB', (64, 48), '#778899').save(output, 'JPEG', exif=exif)
    return output.getvalue()


class PhotoCollectionTests(WorkflowCase):
    def assigned(self, client, asset='F-17'):
        self.start(client)
        if asset == 'V-08':
            with Store(self.data).connection(write=True) as db:
                db.execute("UPDATE tasks SET asset_id='V-08',capability='OBSERVE_POSITION'")
        return client.get('/api/state').json()['task']

    def photo(self, client, task, data=None, request_key=None, purpose='reference-photo', extra=None):
        headers = {**LOCAL, 'Idempotency-Key': request_key or key(),
                   'X-Task-Revision': str(task['revision']), 'Content-Type': 'image/jpeg'}
        if purpose is not None:
            headers['X-Evidence-Purpose'] = purpose
        headers.update(extra or {})
        return client.post(f"/api/tasks/{task['id']}/images", content=jpeg() if data is None else data, headers=headers)

    def test_pressure_photo_is_metadata_stripped_collection_only_idempotent_and_unanalyzable(self):
        from fastapi.testclient import TestClient
        with TestClient(self.application()) as client:
            task = self.assigned(client)
            request_key = key()
            first = self.photo(client, task, request_key=request_key)
            self.assertEqual(first.status_code, 200, first.text)
            self.assertEqual(self.photo(client, task, request_key=request_key).json(), first.json())
            state = client.get('/api/state').json()
            evidence = state['evidence'][0]
            self.assertEqual(evidence['status'], 'collected')
            self.assertEqual(evidence['origin'], 'user-upload')
            self.assertIsNone(evidence['fixture_id'])
            self.assertIsNone(evidence['analysis'])
            self.assertEqual(state['task']['status'], 'awaiting')
            self.assertEqual(len(state['evidence']), 1)
            self.assertEqual(state['photo_collection'], {'version': 1, 'assets': ['F-17', 'V-08']})
            response = client.get(evidence['image_url'])
            self.assertEqual(response.status_code, 200)
            self.assertNotIn(b'PRIVATE_TEST_METADATA', response.content)
            with Image.open(BytesIO(response.content)) as image:
                self.assertEqual(image.format, 'PNG')
                self.assertEqual(image.size, (64, 48))
                self.assertFalse(image.getexif())
            attempted = self.analyze(client, evidence['id'], state['task']['revision'])
            self.assertEqual(attempted.status_code, 409)
            self.assertEqual(attempted.json()['error'], 'photo_analysis_unsupported')
            self.assertFalse(self.calls)
            self.assertFalse(self.ledger.exists())
            self.assertEqual(client.get('/api/state').json(), state)
        with TestClient(self.application(enabled=False)) as restarted:
            restored = restarted.get('/api/state').json()
            self.assertEqual(restored['evidence'], state['evidence'])
            self.assertEqual(restored['task'], state['task'])
            self.assertFalse(self.calls)
            self.assertFalse(self.ledger.exists())

    def test_tagged_valve_photo_does_not_establish_position_and_report_remains_separate(self):
        from fastapi.testclient import TestClient
        with TestClient(self.application()) as client:
            task = self.assigned(client, 'V-08')
            uploaded = self.photo(client, task)
            self.assertEqual(uploaded.status_code, 200)
            state = client.get('/api/state').json()
            self.assertEqual(state['task']['status'], 'awaiting')
            self.assertEqual(state['task']['asset_id'], 'V-08')  # Assignment, not photographed identity.
            self.assertEqual(self.photo(client, task).json()['error'], 'stale_task')
            revision = state['task']['revision']
            report = self.post(client, f"/api/tasks/{task['id']}/reports", {'revision': revision, 'report': 'intermediate'})
            self.assertEqual(report.status_code, 200)
            state = client.get('/api/state').json()
            self.assertEqual([e['kind'] for e in state['evidence']], ['image', 'report'])
            self.assertEqual([e['status'] for e in state['evidence']], ['collected', 'accepted'])
            self.assertEqual(state['evidence'][1]['origin'], 'human-report')
            self.assertEqual(state['task']['status'], 'observed')
            self.assertFalse(self.calls)
            self.assertFalse(self.ledger.exists())

    def test_unsupported_purposes_types_size_and_valve_analysis_are_not_silently_broadened(self):
        from fastapi.testclient import TestClient
        with TestClient(self.application()) as client:
            task = self.assigned(client, 'V-08')
            self.assertEqual(self.photo(client, task, purpose=None).status_code, 400)
            self.assertEqual(self.photo(client, task, purpose='analog-reading').status_code, 400)
            self.assertEqual(self.photo(client, task, extra={'X-Fixture-Id': 'panel-a'}).status_code, 400)
            self.assertEqual(self.photo(client, task, data=b'bad').status_code, 400)
            self.assertEqual(self.photo(client, task, data=b'x'*(2*1024*1024+1)).status_code, 413)
            self.assertEqual(self.photo(client, task, extra={'Content-Type': 'image/heic'}).status_code, 415)
            self.assertFalse(client.get('/api/state').json()['evidence'])
            self.assertFalse(self.calls)

    def test_unreadable_valve_uses_existing_cannot_determine_report_contract(self):
        from fastapi.testclient import TestClient
        with TestClient(self.application()) as client:
            task = self.assigned(client, 'V-08')
            result = self.post(client, f"/api/tasks/{task['id']}/reports", {'revision': task['revision'], 'report': 'unreadable'})
            self.assertEqual(result.status_code, 400)
            result = self.post(client, f"/api/tasks/{task['id']}/reports", {'revision': task['revision'], 'report': 'cannot determine'})
            self.assertEqual(result.status_code, 200)
            state = client.get('/api/state').json()
            self.assertEqual(state['evidence'][0]['status'], 'refused')
            self.assertEqual(state['evidence'][0]['report'], 'cannot determine')
            self.assertIsNone(state['evidence'][0]['analysis'])
            self.assertEqual(state['task']['status'], 'needs_evidence')

    def test_photo_cannot_supply_simulated_correction_prerequisites(self):
        from fastapi.testclient import TestClient
        with TestClient(self.application()) as client:
            self.post(client, '/api/simulation/start', {})
            with Store(self.data).connection(write=True) as db:
                incident = db.execute('SELECT id FROM incidents').fetchone()[0]
                db.execute("INSERT INTO tasks(id,incident_id,revision,status,created_at) VALUES(?,?,1,'awaiting','offline-test')", (key(), incident))
            task = client.get('/api/state').json()['task']
            self.assertEqual(self.photo(client, task).status_code, 200)
            state = client.get('/api/state').json()
            self.assertFalse(state['journey']['observations'])
            self.assertIn('F-17_missing', state['journey']['assessment']['blockers'])
            result = self.post(client, '/api/simulation/approve', {'revision': state['incident']['revision'],
                'action_id': 'SIMULATE_F17_FILTER_REPLACEMENT', 'decision': 'approve'})
            self.assertEqual(result.status_code, 409)
            self.assertEqual(state['journey']['maintenance_status'], 'not_completed')
            self.assertFalse(self.calls)

    def test_legacy_fixture_fingerprint_and_native_analysis_reservation_are_unchanged(self):
        from fastapi.testclient import TestClient
        with TestClient(self.application()) as client:
            task = self.assigned(client)
            request_key = key()
            first = self.upload(client, task, request_key=request_key)
            self.assertEqual(self.upload(client, task, request_key=request_key).json(), first.json())
            state = client.get('/api/state').json()
            self.assertEqual(state['evidence'][0]['status'], 'pending')
            self.assertEqual(state['evidence'][0]['origin'], 'synthetic-fixture')
            self.assertEqual(self.photo(client, task, request_key=request_key).json()['error'], 'idempotency_conflict')
            # Keep real inference out of this test: reservation itself is the existing boundary.
            engine = client.app.state.engine
            aid, created = engine.workflow.reserve_analysis(first.json()['evidence_id'], state['task']['revision'], key())
            self.assertTrue(created)
            self.assertIsInstance(aid, str)
            self.assertFalse(self.calls)

    def test_camera_orientation_applied_before_metadata_removal(self):
        from faulttrace.workflow.uploads import validate_upload
        data=BytesIO(); exif=Image.Exif(); exif[274]=6
        Image.new('RGB',(64,48),'#778899').save(data,'JPEG',exif=exif)
        clean=validate_upload(data.getvalue(),'image/jpeg')
        self.assertEqual((clean['width'],clean['height']),(48,64))
        with Image.open(BytesIO(clean['bytes'])) as image:
            self.assertEqual(image.size,(48,64))
            self.assertFalse(image.getexif())
