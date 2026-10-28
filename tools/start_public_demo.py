"""Fail-closed single-process public package launcher; no service provisioning."""
import os
from pathlib import Path
import sys
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def configuration(environment):
    origin = environment.get('FAULTTRACE_DEMO_ORIGIN', '')
    url = urlsplit(origin)
    if (url.scheme != 'https' or not url.hostname or url.path or url.query or url.fragment
            or url.username or url.password or url.port not in (None, 443)):
        raise ValueError('https_origin_required')
    if environment.get('FAULTTRACE_DEMO_LOCAL_HTTP') not in (None, '', '0'):
        raise ValueError('local_http_forbidden')
    raw = environment.get('FAULTTRACE_DEMO_ROOT', '')
    root = Path(raw)
    if not raw or not root.is_absolute() or root.resolve() == ROOT or ROOT.is_relative_to(root.resolve()):
        raise ValueError('absolute_private_data_root_required')
    if environment.get('FAULTTRACE_PERSISTENT_STORAGE_CONFIRMED') != '1':
        raise ValueError('persistent_storage_confirmation_required')
    port = int(environment.get('PORT', '10000'))
    if not 1024 <= port <= 65535:
        raise ValueError('invalid_port')
    if environment.get('WEB_CONCURRENCY', '1') != '1':
        raise ValueError('single_worker_required')
    return port


def main():
    try:
        port = configuration(os.environ)
        if os.name != 'nt':
            os.umask(0o077)
            if os.geteuid() == 0:
                mount = Path('/var/lib/faulttrace')
                if not Path(os.environ['FAULTTRACE_DEMO_ROOT']).resolve().is_relative_to(mount):
                    raise ValueError('container_private_mount_required')
                mount.mkdir(mode=0o700, exist_ok=True)
                os.chown(mount, 10001, 10001)  # No recursive ownership/history changes.
                os.setgroups([])
                os.setgid(10001)
                os.setuid(10001)
        from faulttrace.workflow.public_app import create_public_app
        import uvicorn
        app = create_public_app()
        uvicorn.run(app, host='0.0.0.0', port=port, workers=1, access_log=False,
                    log_level='critical', proxy_headers=False, server_header=False)
        return 0
    except KeyboardInterrupt:
        return 0
    except Exception:
        print('public_startup_failed: check HTTPS origin, private persistent root, build and single-worker configuration')
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
