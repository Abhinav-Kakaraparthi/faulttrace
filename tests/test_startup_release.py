"""Independently expected startup isolation and occupied-port behavior."""
from pathlib import Path
import http.client
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import unittest

from faulttrace.workflow.startup import fresh_directory, reserve_listener
from faulttrace.workflow.auth import initialize_registry
from faulttrace.workflow.auth_admin import issue

ROOT = Path(__file__).resolve().parents[1]


class StartupTests(unittest.TestCase):
    def test_fresh_directories_preserve_existing_data(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            old = root / '.local' / 'workflow'
            old.mkdir(parents=True)
            sentinel = old / 'historical.bin'
            sentinel.write_bytes(b'historical sentinel')
            first, second = fresh_directory(root), fresh_directory(root)
            self.assertNotEqual(first, second)
            self.assertEqual(first.parent, root / '.local' / 'release-rehearsal')
            self.assertEqual(list(first.iterdir()), [])
            self.assertEqual(sentinel.read_bytes(), b'historical sentinel')

    def test_port_validation(self):
        for port in (True, 8829, 8840, '8830', None):
            with self.subTest(port=port), self.assertRaisesRegex(ValueError, 'invalid_release_port'):
                reserve_listener(port)

    def test_occupied_port_is_preserved(self):
        listener = None
        for port in range(8830, 8840):
            try:
                listener = reserve_listener(port)
                break
            except ValueError:
                continue
        if listener is None:
            self.skipTest('all authorized test ports occupied; existing listeners preserved')
        with listener:
            with self.assertRaisesRegex(ValueError, 'release_port_unavailable'):
                reserve_listener(port)
            # The original socket remains bound and listening after refusal.
            self.assertEqual(listener.getsockname(), ('127.0.0.1', port))
            self.assertEqual(listener.getsockopt(socket.SOL_SOCKET, socket.SO_ACCEPTCONN), 1)


class LauncherTests(unittest.TestCase):
    def test_missing_configuration_is_sanitized_and_creates_no_run(self):
        env = dict(os.environ)
        env.pop('FAULTTRACE_AUTH_REGISTRY', None)
        result = subprocess.run([sys.executable, 'tools/start_release.py'], cwd=ROOT,
                                env=env, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 2)
        self.assertIn('release_startup_failed', result.stdout)
        self.assertNotIn('Traceback', result.stdout + result.stderr)

    def test_real_loopback_start_is_authenticated_and_inference_disabled(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            registry = initialize_registry(root / 'registry.json')
            token_file = root / 'delivery.token'
            issue(registry, 'synthetic', 'commander', 1, True, token_file)
            token = token_file.read_text()
            port = None
            for candidate in range(8830, 8840):
                try:
                    with reserve_listener(candidate):
                        port = candidate
                    break
                except ValueError:
                    continue
            if port is None:
                self.skipTest('all authorized ports occupied; existing servers preserved')
            env = dict(os.environ, FAULTTRACE_AUTH_REGISTRY=str(registry.path), FAULTTRACE_ALLOW_INFERENCE='1')
            env.pop('NEBIUS_API_KEY', None)
            process = subprocess.Popen([sys.executable, 'tools/start_release.py', '--port', str(port)],
                cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            try:
                for attempt in range(100):
                    try:
                        connection = http.client.HTTPConnection('127.0.0.1', port, timeout=1)
                        connection.request('GET', '/api/state')
                        response = connection.getresponse()
                        response.read()
                        connection.close()
                        break
                    except OSError:
                        if process.poll() is not None:
                            self.fail('rehearsal process exited before readiness')
                        time.sleep(.1)
                else:
                    self.fail('rehearsal readiness timeout')
                self.assertEqual(response.status, 401)
                connection = http.client.HTTPConnection('127.0.0.1', port, timeout=2)
                connection.request('GET', '/api/state', headers={'Authorization': 'Bearer ' + token})
                response = connection.getresponse()
                state = json.loads(response.read())
                connection.close()
                self.assertEqual(response.status, 200)
                self.assertFalse(state['inference_enabled'])
                self.assertIsNone(state['incident'])
            finally:
                process.terminate()  # Only the child created by this test.
                stdout, stderr = process.communicate(timeout=10)
                self.assertNotIn(token, stdout + stderr)
