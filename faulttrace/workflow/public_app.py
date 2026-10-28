"""One-origin compiled frontend + isolated demo API; never serves repository files."""
from contextlib import asynccontextmanager
import os
from pathlib import Path
from urllib.parse import urlsplit

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .demo_app import create_demo

CSP = ("default-src 'none'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
       "img-src 'self' blob: data:; font-src 'self'; connect-src 'self'; "
       "base-uri 'self'; form-action 'self'; frame-ancestors 'none'; object-src 'none'")


def create_public_app(demo=None, frontend=None, origin=None):
    """Explicit injected app/build only for offline tests; production uses env."""
    origin = origin or os.environ.get('FAULTTRACE_DEMO_ORIGIN', '')
    host = urlsplit(origin).hostname
    if not host:
        raise ValueError('public_origin_required')
    directory = Path(frontend or os.environ.get('FAULTTRACE_FRONTEND_DIST', 'frontend/dist')).resolve()
    if not (directory / 'index.html').is_file() or not (directory / 'assets').is_dir():
        raise ValueError('compiled_frontend_required')
    child = demo if demo is not None else create_demo()

    @asynccontextmanager
    async def lifespan(app):
        async with child.router.lifespan_context(child):
            yield

    app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=[host, '127.0.0.1', 'localhost', 'testserver'])

    @app.middleware('http')
    async def headers(request, call_next):
        response = await call_next(request)
        response.headers.update({'Content-Security-Policy': CSP, 'X-Frame-Options': 'DENY',
            'X-Content-Type-Options': 'nosniff', 'Referrer-Policy': 'no-referrer',
            'Permissions-Policy': 'camera=(self), microphone=(), geolocation=()'})
        if urlsplit(origin).scheme == 'https':
            response.headers['Strict-Transport-Security'] = 'max-age=31536000'
        return response

    @app.get('/healthz')
    def health():
        return JSONResponse({'status': 'ok'}, headers={'Cache-Control': 'no-store'})

    async def dispatch(scope, receive, send):
        path = scope['path']
        if path == '/api' or path.startswith('/api/'):
            await child(scope, receive, send)
            return
        if scope['method'] not in ('GET', 'HEAD'):
            await JSONResponse({'error': 'method_not_allowed'}, 405)(scope, receive, send)
            return
        if path in ('/', '/commander', '/operator'):
            response = FileResponse(directory / 'index.html', media_type='text/html',
                                    headers={'Cache-Control': 'no-store'})
        else:
            candidate = (directory / path.lstrip('/')).resolve()
            safe = (candidate.is_relative_to(directory) and candidate.is_file()
                and (path.startswith('/assets/') or path in ('/favicon.ico', '/favicon.svg'))
                and candidate.suffix.lower() in ('.js', '.css', '.svg', '.ico', '.png', '.woff2'))
            response = FileResponse(candidate) if safe else JSONResponse({'error': 'not_found'}, 404)
        await response(scope, receive, send)

    # Dispatch preserves /api prefix; a mounted child route would strip it.
    app.mount('/', dispatch)
    return app
