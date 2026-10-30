"""Runtime-only hosting secrets; no provider or platform connections."""
from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools import start_public_demo as launcher


class RuntimeCredentialTests(unittest.TestCase):
    def setUp(self):
        self.directory = self.enterContext(tempfile.TemporaryDirectory())
        self.secret = Path(self.directory)/'faulttrace-runtime.json'
        self.enterContext(patch.object(launcher, 'RUNTIME_SECRET', self.secret))
        self.values = {name: 'sentinel-'+name for name in (
            'NEBIUS_API_KEY', 'TAVILY_API_KEY', 'LANGSMITH_API_KEY')}

    def environment(self):
        return {'FAULTTRACE_RUNTIME_SECRETS_FILE': str(self.secret)}

    def test_optional_offline_and_valid_runtime_load_is_silent(self):
        env = {}
        launcher.load_runtime_credentials(env)
        self.assertEqual(env, {})
        self.secret.write_text(json.dumps(self.values))
        env = self.environment()
        output = StringIO()
        with redirect_stdout(output):
            launcher.load_runtime_credentials(env)
        self.assertEqual(output.getvalue(), '')
        self.assertTrue(all(env[k] == v for k,v in self.values.items()))

    def test_invalid_files_never_partially_install_credentials(self):
        payloads = [b'{', b'[]', b'null', b'x'*16385,
            b'{"NEBIUS_API_KEY":"one","NEBIUS_API_KEY":"two"}',
            json.dumps(dict(self.values, UNEXPECTED='sentinel-private')).encode(),
            json.dumps({'NEBIUS_API_KEY': 'sentinel-private'}).encode()]
        for value in (True, 1, None, '', ' padded ', 'line\nbreak', 'null\0byte', 'x'*4097):
            payloads.append(json.dumps(dict(self.values, TAVILY_API_KEY=value)).encode())
        for raw in payloads:
            with self.subTest(size=len(raw)):
                self.secret.write_bytes(raw)
                env = self.environment()
                with self.assertRaises(ValueError) as error:
                    launcher.load_runtime_credentials(env)
                self.assertNotIn('sentinel', str(error.exception))
                self.assertEqual(env, self.environment())

    def test_location_and_existing_environment_fail_closed(self):
        with self.assertRaisesRegex(ValueError, '^invalid_runtime_secret_location$'):
            launcher.load_runtime_credentials({'FAULTTRACE_RUNTIME_SECRETS_FILE': '/tmp/arbitrary'})
        self.secret.write_text(json.dumps(self.values))
        env = dict(self.environment(), NEBIUS_API_KEY='existing-secret')
        with self.assertRaisesRegex(ValueError, '^ambiguous_runtime_credentials$'):
            launcher.load_runtime_credentials(env)
        self.assertNotIn('TAVILY_API_KEY', env)

    def test_launcher_failure_does_not_print_arbitrary_exception(self):
        output = StringIO()
        with patch.object(launcher, 'configuration', return_value=10000), \
                patch.object(launcher, 'load_runtime_credentials', side_effect=ValueError('sentinel-secret')), \
                redirect_stdout(output):
            self.assertEqual(launcher.main(), 2)
        self.assertNotIn('sentinel-secret', output.getvalue())
        self.assertIn('public_startup_failed:', output.getvalue())

    def test_secret_is_explicitly_excluded_from_docker_build_context(self):
        root = Path(__file__).resolve().parents[1]
        self.assertIn('**/faulttrace-runtime.json', (root/'.dockerignore').read_text().splitlines())
        docker = (root/'Dockerfile').read_text()
        for name in self.values:
            self.assertNotIn('ARG '+name, docker)
            self.assertNotIn('ENV '+name, docker)


if __name__ == '__main__':
    unittest.main()
