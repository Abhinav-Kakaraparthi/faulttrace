"""Run a fresh local-only, inference-disabled authenticated release rehearsal."""
import argparse
import asyncio
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8830)
    args = parser.parse_args(argv)
    listener = None
    try:
        from faulttrace.workflow.auth import Registry
        from faulttrace.workflow.startup import fresh_directory, reserve_listener
        from faulttrace.workflow.api import create_app
        import uvicorn
        registry_path = os.environ.get('FAULTTRACE_AUTH_REGISTRY')
        if not registry_path:
            raise ValueError('auth_configuration_required')
        Registry(registry_path)
        listener = reserve_listener(args.port)
        directory = fresh_directory()
        app = create_app(directory / 'data', directory / 'usage.json', enabled=False,
                         profile='release', auth_registry=registry_path)
        config = uvicorn.Config(app, host='127.0.0.1', port=args.port, workers=1,
                                access_log=False, log_level='critical')
        print(f'release_rehearsal_ready port={args.port} inference=off')
        asyncio.run(uvicorn.Server(config).serve(sockets=[listener]))
        return 0
    except KeyboardInterrupt:
        return 0
    except Exception:
        print('release_startup_failed: verify private auth configuration and available port')
        return 2
    finally:
        if listener:
            listener.close()


if __name__ == '__main__':
    raise SystemExit(main())
