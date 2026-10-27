"""Local administrator CLI. Never exposes issuance or grant mutation via HTTP."""
import argparse
import hashlib
import os
from pathlib import Path
import secrets
import time

from .auth import Registry, initialize_registry
from .storage import ROOT, identifier


def private_path(value):
    path = Path(value).resolve()
    if not path.is_relative_to((ROOT / '.local').resolve()):
        raise ValueError('private_path_must_be_under_local')
    return path


def issue(registry, principal, role, hours, create, token_file):
    if not 0 < hours <= 24 * 30 or (create and role != 'commander'):
        raise ValueError('invalid_credential_options')
    token = secrets.token_urlsafe(32)
    # Exclusive delivery file: token never goes to argv, terminal/log output or registry.
    token_file = Path(token_file)
    token_file.parent.mkdir(parents=True, exist_ok=True)
    with registry.edit() as value:
        if principal in value['principals']:
            raise ValueError('principal_already_exists')
        value['principals'][principal] = {'token_hash': hashlib.sha256(token.encode()).hexdigest(),
            'role': role, 'expires': time.time() + hours * 3600, 'revoked': False,
            'create': create, 'incidents': []}
        # Validate before writing the credential delivery file.
        from .auth import require
        import re
        require(re.fullmatch(r'[A-Za-z0-9_-]{1,64}', principal))
        with token_file.open('x', encoding='ascii') as stream:
            os.chmod(token_file, 0o600)
            stream.write(token)


def grant(registry, principal, incident, assign=False):
    identifier(incident)
    with registry.edit() as value:
        p = value['principals'][principal]
        if assign and p['role'] != 'operator':
            raise ValueError('operator_required')
        if incident not in p['incidents']:
            p['incidents'].append(incident)
        if assign:
            value['operators'][incident] = principal


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registry', required=True)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('init')
    create = sub.add_parser('issue')
    create.add_argument('--principal', required=True)
    create.add_argument('--role', choices=['commander', 'operator'], required=True)
    create.add_argument('--hours', type=float, required=True)
    create.add_argument('--create', action='store_true')
    create.add_argument('--token-file', required=True)
    revoke = sub.add_parser('revoke')
    revoke.add_argument('--principal', required=True)
    for action in ('grant', 'assign-operator'):
        command = sub.add_parser(action)
        command.add_argument('--principal', required=True)
        command.add_argument('--incident', required=True)
    args = parser.parse_args(argv)
    try:
        path = private_path(args.registry)
        if args.command == 'init':
            initialize_registry(path)
        else:
            registry = Registry(path)
            if args.command == 'issue':
                issue(registry, args.principal, args.role, args.hours, args.create, private_path(args.token_file))
            elif args.command == 'revoke':
                with registry.edit() as value:
                    value['principals'][args.principal]['revoked'] = True
            else:
                grant(registry, args.principal, args.incident, args.command == 'assign-operator')
        print('administrator_operation_completed')
        return 0
    except Exception:
        print('administrator_operation_failed')
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
