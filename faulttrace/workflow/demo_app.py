"""Cookie-authenticated isolated judge demo gateway; provider inference stays off."""
import asyncio
from contextlib import AsyncExitStack, asynccontextmanager
import os
from pathlib import Path
import time
from urllib.parse import urlsplit

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from starlette.middleware.trustedhost import TrustedHostMiddleware
import httpx

from .api import bounded_body, fields
from .demo_runtime import assign, open_run
from .demo_sessions import DemoSessions
from .storage import InstanceLock, WorkflowError, identifier
from .uploads import MAX_UPLOAD


def create_demo_app(directory, origin, *, local_http=False, clock=time.time, ttl=7200, limit=32,
                    live=False, budget=None, send=None, key_source=None):
    url = urlsplit(origin)
    if (url.path or url.query or url.fragment or url.username or url.password
            or not url.hostname or url.scheme not in ('http', 'https')
            or (url.scheme == 'http' and not (local_http and url.hostname in ('127.0.0.1', 'localhost')))):
        raise ValueError('invalid_demo_origin')
    secure = url.scheme == 'https'
    # Browsers share cookies across ports. New local previews must not clobber
    # the session of an older localhost service using the legacy cookie name.
    cookie_name = '__Host-faulttrace_demo' if secure else 'faulttrace_demo_local_' + str(url.port or 80)
    cookie_path = '/' if secure else '/api'
    root = Path(directory)
    if live and not budget:
        raise ValueError('live_spending_reservations_required')
    children, locks = {}, {}
    pool_lock = asyncio.Lock()
    upload_slots = asyncio.Semaphore(2)

    @asynccontextmanager
    async def upload_slot(required):
        if not required:
            yield
        else:
            if upload_slots.locked():
                raise WorkflowError('demo_upload_capacity', 429)
            async with upload_slots:
                yield

    @asynccontextmanager
    async def lifespan(app):
        root.mkdir(parents=True, exist_ok=True)
        lock = InstanceLock(root / 'demo-instance.lock')
        try:
            async with AsyncExitStack() as stack:
                app.state.sessions = DemoSessions(root, clock=clock, ttl=ttl, limit=limit, live=live)
                if budget:
                    budget.recover_pending()
                app.state.stack = stack
                yield
        finally:
            children.clear()
            locks.clear()
            lock.close()

    app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=[url.hostname, '127.0.0.1', 'localhost', 'testserver'])

    async def runtime(run, session, run_live):
        async with pool_lock:
            if run not in children:
                child, registry = await open_run(app.state.stack, root / 'runs' / identifier(run), origin,
                    live=run_live, budget=budget.for_session(session) if budget and run_live else None,
                    send=send, key_source=key_source)
                child.state.continuation.allowed = lambda: app.state.sessions.continuation_active(session, run)
                client = await app.state.stack.enter_async_context(httpx.AsyncClient(
                    transport=httpx.ASGITransport(app=child), base_url='http://127.0.0.1'))
                children[run] = child, registry, client
            return children[run]

    def cookie(response, token):
        response.set_cookie(cookie_name, token, max_age=ttl, path=cookie_path,
                            httponly=True, secure=secure, samesite='strict')

    @app.middleware('http')
    async def boundary(request, call_next):
        try:
            if (request.headers.get('x-faulttrace-demo') != '1'
                    or request.headers.get('sec-fetch-site') not in (None, 'same-origin', 'none')
                    or request.headers.get('origin') not in (None, origin)):
                raise WorkflowError('demo_origin_required', 403)
            if request.method not in ('GET', 'HEAD') and request.headers.get('origin') != origin:
                raise WorkflowError('demo_origin_required', 403)
            if request.headers.get('authorization'):
                raise WorkflowError('access_denied', 403)
            response = await call_next(request)
        except WorkflowError as error:
            response = JSONResponse({'error': error.code}, error.status)
            if error.status == 401:
                response.delete_cookie(cookie_name, path=cookie_path, secure=secure, httponly=True, samesite='strict')
        except Exception:
            response = JSONResponse({'error': 'storage_or_internal_failure'}, 500)
        response.headers.update({'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff',
                                 'Referrer-Policy': 'no-referrer', 'X-Frame-Options': 'DENY'})
        return response

    @app.api_route('/api/{path:path}', methods=['GET', 'POST', 'PUT', 'DELETE', 'HEAD', 'OPTIONS'])
    async def api(request: Request, path: str):
        sessions = app.state.sessions
        token = request.cookies.get(cookie_name)
        if path == 'demo/session' and request.method == 'GET':
            if token:
                row = sessions.get(token)
                return JSONResponse(sessions.public(row))
            token, row = sessions.new()
            response = JSONResponse(sessions.public(row))
            cookie(response, token)
            return response
        row = sessions.get(token)
        # Serialize this visitor's switch/restart and workflow requests. A stale
        # tab cannot send an old-context mutation into a replacement investigation.
        lock = locks.setdefault(row['hash'], asyncio.Lock())
        async with lock:
            row = sessions.get(token)
            if request.method != 'GET':
                sessions.check_csrf(row, request.headers.get('x-csrf-token'))
            prior = request.headers.get('x-faulttrace-demo-run', '')
            if path in ('demo/start', 'demo/restart', 'demo/restart-offline') and request.method == 'POST':
                await fields(request, [])
                row = sessions.change(token, request.headers.get('idempotency-key'), path.split('/')[1], prior)
                await runtime(row['run'], row['hash'], sessions.public(row)['inference_enabled'])
                return JSONResponse(sessions.public(row))
            if prior != row['run'] or not row['run']:
                raise WorkflowError('demo_session_changed', 409)
            if path == 'demo/end' and request.method == 'POST':
                await fields(request, [])
                sessions.end(row)
                response = JSONResponse({'ended': True})
                response.delete_cookie(cookie_name, path=cookie_path, secure=secure, httponly=True, samesite='strict')
                return response
            run_live = sessions.public(row)['inference_enabled']
            child, registry, client = await runtime(row['run'], row['hash'], run_live)
            role = request.headers.get('x-faulttrace-workspace')
            if role not in ('commander', 'operator'):
                raise WorkflowError('access_denied', 403)
            if path == 'demo/observations' and request.method == 'POST':
                if run_live:
                    raise WorkflowError('offline_template_only', 403)
                if role != 'commander':
                    raise WorkflowError('access_denied', 403)
                value = await fields(request, ['action_id', 'revision'])
                result = assign(child, value['action_id'], value['revision'], request.headers.get('idempotency-key'))
                return JSONResponse({'assignment_id': result})
            if path.startswith('demo/'):
                raise WorkflowError('access_denied', 403)
            if request.method == 'POST' and path.endswith('/images'):
                with child.state.workflow.store.connection() as db:
                    replay = db.execute('SELECT 1 FROM operations WHERE key=?', (request.headers.get('idempotency-key'),)).fetchone()
                    if not replay and db.execute("SELECT COUNT(*) FROM evidence WHERE kind='image'").fetchone()[0] >= 4:
                        raise WorkflowError('demo_upload_limit', 429)
            headers = {k: v for k, v in request.headers.items() if k in (
                'content-type', 'idempotency-key', 'origin', 'x-task-revision', 'x-fixture-id', 'x-evidence-purpose')}
            headers['authorization'] = 'Bearer ' + registry.tokens[role]
            async with upload_slot(request.method == 'POST' and path.endswith('/images')):
                body = await bounded_body(request, MAX_UPLOAD)
                result = await client.request(request.method, '/api/' + path, headers=headers, content=body)
            if path == 'state' and result.status_code == 200:
                from .planner_contract import build_context, permitted_actions
                value = result.json()
                with child.state.workflow.store.connection() as db:
                    value['demo'] = {'template_actions': list(permitted_actions(build_context(db))),
                        'assignment_remaining': max(0, 4-db.execute("SELECT COUNT(*) FROM events WHERE kind='demo_template_assigned'").fetchone()[0]),
                        'live': run_live, 'spending': budget.summary(row['hash']) if budget else None}
                return JSONResponse(value)
            return Response(result.content, result.status_code,
                            headers={'Content-Type': result.headers.get('content-type', 'application/json')})

    return app


def create_demo():
    directory, origin = os.environ.get('FAULTTRACE_DEMO_ROOT'), os.environ.get('FAULTTRACE_DEMO_ORIGIN')
    if not directory or not origin:
        raise ValueError('explicit_demo_configuration_required')
    live = os.environ.get('FAULTTRACE_DEMO_LIVE') == '1'
    budget = None
    if live:
        if os.environ.get('FAULTTRACE_ALLOW_INFERENCE') != '1' or not (os.environ.get('NEBIUS_API_KEY') or '').strip():
            raise ValueError('explicit_live_opt_in_and_credentials_required')
        from .spending import Spending
        budget = Spending(directory)
    return create_demo_app(directory, origin, local_http=os.environ.get('FAULTTRACE_DEMO_LOCAL_HTTP') == '1', live=live, budget=budget)
