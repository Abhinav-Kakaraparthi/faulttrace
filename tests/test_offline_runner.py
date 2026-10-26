"""Verify the CI guard without contacting providers or other external hosts."""
import os
from pathlib import Path
import socket
import subprocess
import sys
import unittest
from types import SimpleNamespace

from tools.run_offline_tests import loopback, network_guard


class OfflineRunnerTests(unittest.TestCase):
    def test_guard_blocks_provider_dns_tcp_and_udp_with_fixed_diagnostic(self):
        sock = SimpleNamespace(family=socket.AF_INET)
        for event, args in (
            ('socket.getaddrinfo', ('api.tokenfactory.nebius.com', 443, 0, 0, 0)),
            ('socket.gethostbyname', ('api.tokenfactory.nebius.com',)),
            ('socket.gethostbyaddr', ('203.0.113.1',)),
            ('socket.connect', (sock, ('203.0.113.1', 443))),
            ('socket.sendto', (sock, ('203.0.113.1', 443))),
            ('socket.sendmsg', (sock, ('203.0.113.1', 443))),
        ):
            with self.subTest(event=event):
                blocked = []
                with self.assertRaisesRegex(PermissionError, '^external_network_forbidden$'):
                    network_guard(blocked)(event, args)
                self.assertEqual(blocked, [1])

    def test_local_ipc_and_loopback_remain_available_for_asgi(self):
        blocked = []
        guard = network_guard(blocked)
        for host in ('127.0.0.1', '::1', 'localhost', b'127.0.0.1', None):
            self.assertTrue(loopback(host))
            guard('socket.getaddrinfo', (host, 80, 0, 0, 0))
        guard('socket.connect', (SimpleNamespace(family=socket.AF_INET), ('127.0.0.1', 80)))
        if hasattr(socket, 'AF_UNIX'):
            guard('socket.connect', (SimpleNamespace(family=socket.AF_UNIX), 'local-socket'))
        guard('unrelated.event', ())
        self.assertFalse(loopback('not-a-local-host'))
        self.assertEqual(blocked, [])

    def test_caught_external_connection_still_fails_runner_and_removes_credentials(self):
        code = '''
import os, socket, unittest
from tools.run_offline_tests import run_tests
os.environ['NEBIUS_API_KEY'] = 'OFFLINE_RUNNER_SENTINEL'
class Case(unittest.TestCase):
    def runTest(self):
        self.assertNotIn('NEBIUS_API_KEY', os.environ)
        self.assertEqual(os.environ['FAULTTRACE_ALLOW_INFERENCE'], '0')
        with socket.socket() as sock:
            with self.assertRaisesRegex(PermissionError, '^external_network_forbidden$'):
                sock.connect(('203.0.113.1', 443))
raise SystemExit(run_tests(unittest.TestSuite([Case()])))
'''
        env = dict(os.environ)
        env.pop('NEBIUS_API_KEY', None)
        completed = subprocess.run([sys.executable, '-c', code], cwd=Path(__file__).resolve().parents[1],
                                   env=env, capture_output=True, text=True, timeout=20)
        self.assertEqual(completed.returncode, 1)
        self.assertIn('Forbidden external network attempts: 1', completed.stdout)
        self.assertIn('OK', completed.stderr)
        self.assertNotIn('OFFLINE_RUNNER_SENTINEL', completed.stdout + completed.stderr)
