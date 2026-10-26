"""A separately configured preview origin must not weaken local API boundaries."""
from unittest.mock import patch

from fastapi.testclient import TestClient

from faulttrace.workflow.local_origin import DEFAULT_ORIGINS, allowed_origins
from test_workflow_api import FIXTURES, LOCAL, WorkflowCase, key


class PreviewOriginTests(WorkflowCase):
    def test_default_origins_still_reject_unconfigured_test_port(self):
        with patch.dict('os.environ', {}, clear=True):
            self.assertEqual(allowed_origins(), DEFAULT_ORIGINS)
            with TestClient(self.application(enabled=False)) as client:
                response = client.post('/api/incidents', json={}, headers={
                    **LOCAL, 'Origin': 'http://127.0.0.1:5181', 'Idempotency-Key': key()})
                self.assertEqual(response.status_code, 403)
                self.assertEqual(response.json(), {'error': 'origin_not_allowed'})
                self.assertIsNone(client.get('/api/state').json()['incident'])

    def test_configured_origin_uploads_but_analysis_makes_no_provider_call(self):
        with patch.dict('os.environ', {'FAULTTRACE_PREVIEW_ORIGIN': 'http://127.0.0.1:5181'}):
            with TestClient(self.application(enabled=False)) as client:
                task = self.start(client)
                headers = {**LOCAL, 'Origin': 'http://127.0.0.1:5181', 'Idempotency-Key': key(),
                           'X-Task-Revision': str(task['revision']), 'X-Evidence-Purpose': 'reference-photo',
                           'Content-Type': 'image/png'}
                response = client.post(f'/api/tasks/{task["id"]}/images',
                                       content=(FIXTURES / 'panel-a.png').read_bytes(), headers=headers)
                self.assertEqual(response.status_code, 200)
                eid = response.json()['evidence_id']
                current = client.get('/api/state').json()
                self.assertEqual(current['evidence'][0]['status'], 'collected')
                response = client.post(f'/api/evidence/{eid}/analyze-photo',
                                       json={'revision': current['task']['revision']}, headers={
                                           **LOCAL, 'Origin': 'http://127.0.0.1:5181', 'Idempotency-Key': key()})
                self.assertEqual(response.status_code, 403)
                self.assertEqual(response.json(), {'error': 'inference_disabled'})
                self.assertIsNone(client.get('/api/state').json()['evidence'][0]['analysis'])
                self.assertEqual(self.calls, [])

    def test_configured_origin_does_not_allow_another_port_or_skip_local_header(self):
        with patch.dict('os.environ', {'FAULTTRACE_PREVIEW_ORIGIN': 'http://127.0.0.1:5181'}):
            with TestClient(self.application(enabled=False)) as client:
                for headers, error in (({**LOCAL, 'Origin': 'http://127.0.0.1:5182'}, 'origin_not_allowed'),
                                       ({'Origin': 'http://127.0.0.1:5181'}, 'local_client_header_required')):
                    response = client.post('/api/incidents', json={}, headers={**headers, 'Idempotency-Key': key()})
                    self.assertEqual(response.status_code, 403)
                    self.assertEqual(response.json(), {'error': error})
                self.assertIsNone(client.get('/api/state').json()['incident'])

    def test_invalid_origin_configuration_fails_closed_without_echoing_value(self):
        for value in ('', '*', 'https://127.0.0.1:5181', 'http://0.0.0.0:5181',
                      'http://example.com:5181', 'http://localhost:0', 'http://localhost:65536',
                      'http://localhost:5181/', 'http://localhost:5181?secret=value',
                      'http://user:secret@localhost:5181', 'http://localhost:5181\n'):
            with self.subTest(value=value), patch.dict('os.environ', {'FAULTTRACE_PREVIEW_ORIGIN': value}):
                with self.assertRaisesRegex(ValueError, '^invalid_preview_origin$'):
                    self.application(enabled=False)

    def test_explicit_localhost_origin_and_existing_defaults_are_preserved(self):
        with patch.dict('os.environ', {'FAULTTRACE_PREVIEW_ORIGIN': 'http://localhost:5181'}):
            self.assertEqual(allowed_origins(), DEFAULT_ORIGINS | {'http://localhost:5181'})
