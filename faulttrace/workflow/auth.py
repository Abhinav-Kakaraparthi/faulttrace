"""Private, reload-on-request opaque credential registry. No HTTP issuance."""
from contextlib import contextmanager
import hashlib
import json
import math
import os
from pathlib import Path
import re
import secrets
import time

from .storage import InstanceLock, WorkflowError


def require(condition):
    if not condition:
        raise ValueError('invalid_auth_configuration')


class Registry:
    def __init__(self, path):
        self.path = Path(path)
        self.read()  # Validate before any workflow initialization.

    def read(self):
        try:
            value = json.loads(self.path.read_text(encoding='utf-8'))
            require(set(value) == {'version', 'principals', 'operators'} and value['version'] == 1)
            require(isinstance(value['principals'], dict) and isinstance(value['operators'], dict))
            hashes = set()
            for pid, p in value['principals'].items():
                require(re.fullmatch(r'[A-Za-z0-9_-]{1,64}', pid))
                require(set(p) == {'token_hash', 'role', 'expires', 'revoked', 'create', 'incidents'})
                require(re.fullmatch('[0-9a-f]{64}', p['token_hash']) and p['token_hash'] not in hashes)
                hashes.add(p['token_hash'])
                require(p['role'] in ('commander', 'operator'))
                require(type(p['expires']) in (int, float) and math.isfinite(p['expires']))
                require(type(p['revoked']) is bool and type(p['create']) is bool)
                require(not p['create'] or p['role'] == 'commander')
                require(isinstance(p['incidents'], list) and all(isinstance(i, str) for i in p['incidents']))
            for incident, pid in value['operators'].items():
                require(isinstance(incident, str) and value['principals'][pid]['role'] == 'operator')
                require(incident in value['principals'][pid]['incidents'])
            return value
        except Exception:
            raise ValueError('invalid_auth_configuration') from None

    @contextmanager
    def edit(self):
        lock = InstanceLock(self.path.with_suffix('.lock'))
        try:
            value = self.read()
            yield value
            temporary = self.path.with_name(self.path.name + '.' + secrets.token_hex(8))
            try:
                with temporary.open('x', encoding='utf-8') as stream:
                    os.chmod(temporary, 0o600)
                    json.dump(value, stream)
                    stream.flush()
                    os.fsync(stream.fileno())
                Registry(temporary)
                os.replace(temporary, self.path)
            finally:
                temporary.unlink(missing_ok=True)
        finally:
            lock.close()

    def authenticate(self, header):
        if not isinstance(header, str) or not re.fullmatch(r'Bearer [A-Za-z0-9_-]{43,128}', header):
            raise WorkflowError('authentication_required', 401)
        digest = hashlib.sha256(header[7:].encode()).hexdigest()
        try:
            entries = self.read()['principals']
        except ValueError:
            raise WorkflowError('authentication_required', 401) from None
        for pid, p in entries.items():
            if secrets.compare_digest(digest, p['token_hash']) and not p['revoked'] and p['expires'] > time.time():
                return dict(p, principal_id=pid)
        raise WorkflowError('authentication_required', 401)

    def grant_creator(self, pid, incident):
        with self.edit() as value:
            grants = value['principals'][pid]['incidents']
            if incident not in grants:
                grants.append(incident)


def initialize_registry(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        os.chmod(path, 0o600)
        json.dump({'version': 1, 'principals': {}, 'operators': {}}, stream)
    return Registry(path)
