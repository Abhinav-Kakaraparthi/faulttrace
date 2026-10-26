"""Run the complete backend suite without provider credentials or external sockets."""
import ipaddress
import os
from pathlib import Path
import socket
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]


def loopback(host):
    if host in (None, 'localhost', b'localhost'):
        return True
    try:
        if isinstance(host, bytes):
            host = host.decode('ascii')
        return ipaddress.ip_address(host).is_loopback
    except (ValueError, UnicodeError):
        return False


def network_guard(blocked):
    """Audit before DNS/connect/sendto; only local IPC used by ASGI tests is allowed.

    This is a guard against accidental network use in this test process, not a
    security sandbox for hostile tests, native extensions or subprocesses.
    """
    def audit(event, args):
        if event in ('socket.getaddrinfo', 'socket.gethostbyname', 'socket.gethostbyaddr'):
            allowed = loopback(args[0])
        elif event in ('socket.connect', 'socket.sendto', 'socket.sendmsg'):
            sock, address = args
            if sock.family == getattr(socket, 'AF_UNIX', None):
                return  # Unix-domain IPC is local, not a provider connection.
            allowed = isinstance(address, tuple) and loopback(address[0])
        else:
            return
        if not allowed:
            blocked.append(1)  # No hostnames, headers or arbitrary error text.
            raise PermissionError('external_network_forbidden')
    return audit


def run_tests(suite=None):
    os.environ.pop('NEBIUS_API_KEY', None)
    os.environ['FAULTTRACE_ALLOW_INFERENCE'] = '0'
    sys.path.insert(0, str(ROOT))
    blocked = []
    # Install before discovering/importing tests, including their worker threads.
    sys.addaudithook(network_guard(blocked))
    if suite is None:
        suite = unittest.defaultTestLoader.discover(str(ROOT / 'tests'))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(f'Forbidden external network attempts: {len(blocked)}')
    # A provider may catch PermissionError; the whole suite must still fail.
    return int(not result.wasSuccessful() or result.testsRun == 0 or bool(blocked))


if __name__ == '__main__':
    raise SystemExit(run_tests())
