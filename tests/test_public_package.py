"""Compiled public package security and durable cookie restart; no network."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import uuid

from fastapi.testclient import TestClient

from faulttrace.workflow.demo_app import create_demo_app
from faulttrace.workflow.public_app import create_public_app
from tools.start_public_demo import configuration

ORIGIN = 'https://faulttrace.example'


class PublicPackageTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.build = self.root / 'compiled'
        (self.build / 'assets').mkdir(parents=True)
        (self.build / 'index.html').write_text('<html>compiled demo</html>')
        (self.build / 'assets' / 'app.js').write_text('const compiled = true;')
        (self.build / '.env').write_text('private-sentinel')
        (self.build / 'assets' / 'secret.key').write_text('private-key-sentinel')
        self.data = self.root / 'private'

    def app(self):
        child = create_demo_app(self.data, ORIGIN)
        return create_public_app(child, self.build, ORIGIN)

    def test_frontend_routes_headers_api_gate_and_private_files(self):
        with TestClient(self.app(), base_url=ORIGIN) as client:
            for route in ('/', '/commander', '/operator', '/?mode=connected&view=operator'):
                response = client.get(route)
                self.assertEqual(response.status_code, 200)
                self.assertIn('compiled demo', response.text)
                self.assertEqual(response.headers['Cache-Control'], 'no-store')
                self.assertIn("frame-ancestors 'none'", response.headers['Content-Security-Policy'])
                self.assertEqual(response.headers['Strict-Transport-Security'], 'max-age=31536000')
            self.assertEqual(client.get('/assets/app.js').status_code, 200)
            for route in ('/.env', '/assets/secret.key', '/docs', '/assets/../../.env',
                          '/workflow.sqlite3', '/usage.json', '/api/no-such-route'):
                response = client.get(route)
                self.assertIn(response.status_code, (403, 404))
                self.assertNotIn('private-sentinel', response.text)
            self.assertEqual(client.get('/healthz').json(), {'status': 'ok'})
            self.assertEqual(client.get('/api/demo/session').status_code, 403)
            self.assertEqual(client.post('/commander', json={}).status_code, 405)
            self.assertEqual(client.get('/commander', headers={'host':'untrusted.example'}).status_code, 400)

    def test_session_resume_across_package_restart_and_cross_session_denial(self):
        headers = {'X-FaultTrace-Demo':'1', 'Origin':ORIGIN, 'X-FaultTrace-Workspace':'commander'}
        with TestClient(self.app(), base_url=ORIGIN) as client:
            bootstrap = client.get('/api/demo/session', headers=headers)
            self.assertIn('__Host-faulttrace_demo=', bootstrap.headers['set-cookie'])
            self.assertIn('Secure', bootstrap.headers['set-cookie'])
            session = bootstrap.json()
            headers.update({'X-CSRF-Token':session['csrf_token'], 'Idempotency-Key':str(uuid.uuid4())})
            response = client.post('/api/demo/start', headers=headers, json={})
            self.assertEqual(response.status_code, 200)
            session = response.json()
            headers['X-FaultTrace-Demo-Run'] = session['active_run']
            initial = client.get('/api/state', headers=headers).json()
            self.assertFalse(initial['inference_enabled'])
            cookie = client.cookies.get('__Host-faulttrace_demo')
        with TestClient(self.app(), base_url=ORIGIN) as client:
            client.cookies.set('__Host-faulttrace_demo',cookie,domain='faulttrace.example',path='/')
            resumed = client.get('/api/demo/session', headers=headers).json()
            self.assertEqual(resumed['active_run'], session['active_run'])
            state = client.get('/api/state', headers=headers).json()
            self.assertEqual(state['incident'], initial['incident'])
            self.assertEqual(state['task']['id'], initial['task']['id'])
            client.cookies.clear()
            self.assertEqual(client.get('/api/state', headers=headers).status_code, 401)

    def test_build_required_and_fail_closed_launcher(self):
        with self.assertRaisesRegex(ValueError, 'compiled_frontend_required'):
            create_public_app(frontend=self.root/'missing', origin=ORIGIN)
        env = {'FAULTTRACE_DEMO_ORIGIN':ORIGIN, 'FAULTTRACE_DEMO_ROOT':str(self.data),
               'FAULTTRACE_PERSISTENT_STORAGE_CONFIRMED':'1'}
        self.assertEqual(configuration(env),10000)
        for changes in ({'FAULTTRACE_DEMO_ORIGIN':'http://faulttrace.example'},
                        {'FAULTTRACE_PERSISTENT_STORAGE_CONFIRMED':'0'},
                        {'FAULTTRACE_DEMO_ROOT':'relative'}, {'FAULTTRACE_DEMO_LOCAL_HTTP':'1'},
                        {'WEB_CONCURRENCY':'2'}, {'PORT':'80'}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                configuration(dict(env,**changes))


if __name__ == '__main__':
    unittest.main()
