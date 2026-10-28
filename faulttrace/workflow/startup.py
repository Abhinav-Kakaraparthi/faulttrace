"""Fresh, loopback-only release rehearsal resources; never open historical runs."""
from pathlib import Path
import socket
import uuid


ROOT = Path(__file__).resolve().parents[2]


def reserve_listener(port):
    """Keep the socket reserved until uvicorn takes ownership (no probe race)."""
    if type(port) is not int or not 8830 <= port <= 8839:
        raise ValueError('invalid_release_port')
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        if hasattr(socket, 'SO_EXCLUSIVEADDRUSE'):
            listener.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        listener.bind(('127.0.0.1', port))
        listener.listen(128)
        listener.setblocking(False)
        return listener
    except OSError:
        listener.close()
        raise ValueError('release_port_unavailable') from None


def fresh_directory(root=ROOT):
    """No caller-supplied data path, reuse, migration or deletion operation."""
    parent = Path(root) / '.local' / 'release-rehearsal'
    parent.mkdir(parents=True, exist_ok=True)
    directory = parent / uuid.uuid4().hex
    directory.mkdir(exist_ok=False)
    return directory
