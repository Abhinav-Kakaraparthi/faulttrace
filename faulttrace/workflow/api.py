"""Loopback-only local API; raw uploads and logs never include the provider key."""
from contextlib import asynccontextmanager
import asyncio
import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from starlette.concurrency import run_in_threadpool
from starlette.middleware.trustedhost import TrustedHostMiddleware

from faulttrace.ledger import DEFAULT_LEDGER
from faulttrace.provider import transport
from faulttrace.validation import parse_json

from .journey import Journey
from .local_origin import allowed_origins
from .analysis import AnalysisEngine, source_revision
from .service import Workflow
from .storage import DEFAULT_DATA, InstanceLock, Store, WorkflowError, identifier
from .uploads import MAX_UPLOAD, validate_upload


async def bounded_body(request, limit):
    body = bytearray()
    async for chunk in request.stream():
        if len(body) + len(chunk) > limit:
            raise WorkflowError("request_too_large", 413)
        body.extend(chunk)
    return bytes(body)


async def fields(request, expected):
    try:
        value = parse_json((await bounded_body(request, 16384)).decode("utf-8"))
        if not isinstance(value, dict) or set(value) != set(expected):
            raise ValueError()
        if "revision" in value and type(value["revision"]) is not int:
            raise ValueError()
        return value
    except WorkflowError:
        raise
    except Exception:
        raise WorkflowError("invalid_request", 400) from None


def create_app(directory=DEFAULT_DATA, ledger_path=DEFAULT_LEDGER, send=transport,
               enabled=None, key_source=None, simulation_clock=None, simulation_outcome="effective", test_output=False,
               profile='local', auth_registry=None, demo_registry=None, browser_origin=None, budget=None,
               documentation_options=None):
    if profile not in ('local', 'release', 'demo'):
        raise ValueError('invalid_profile')
    from .auth import Registry
    from .access import Access
    if profile == 'release' and not auth_registry:
        raise ValueError('auth_configuration_required')
    registry = Registry(auth_registry) if profile == 'release' else None
    if profile == 'demo':
        from .demo_runtime import DemoRegistry
        if not isinstance(demo_registry, DemoRegistry) or (enabled is not False and not (enabled is True and budget)):
            raise ValueError('invalid_demo_configuration')
        registry = demo_registry
    if test_output and send is transport:
        raise ValueError('test_output_requires_provider_double')
    origins = allowed_origins()
    if profile == 'demo':
        origins = origins | {browser_origin}
    inference_enabled = (os.environ.get("FAULTTRACE_ALLOW_INFERENCE") == "1") if enabled is None else enabled

    @asynccontextmanager
    async def lifespan(app):
        Path(directory).mkdir(parents=True, exist_ok=True)
        lock = InstanceLock(Path(directory) / "instance.lock")
        kwargs = {} if key_source is None else {"key_source": key_source}
        engine = None
        try:
            store = Store(directory)
            workflow = Workflow(store)
            engine = AnalysisEngine(workflow, ledger_path, send, inference_enabled, revision=source_revision(), budget=budget, **kwargs)
            app.state.workflow, app.state.engine = workflow, engine
            app.state.journey = Journey(workflow, simulation_clock, simulation_outcome, test_output, demo_time=profile == 'demo')
            from .walkthrough import RecoveryMonitor
            app.state.monitor = RecoveryMonitor(app.state.journey)
            app.state.access = Access(store, registry) if registry else None
            async def monitor():
                while True:
                    try:
                        status = app.state.monitor.snapshot()
                        if not status or status['status'] != 'running':
                            return
                        await asyncio.sleep(.25)
                        await run_in_threadpool(app.state.monitor.step)
                    except Exception:
                        app.state.monitor.fail()
                        return
            task = None
            def start_monitor():
                nonlocal task
                status = app.state.monitor.snapshot()
                if status and status['status'] == 'running' and (task is None or task.done()):
                    task = asyncio.create_task(monitor())
            app.state.start_monitor = start_monitor
            start_monitor()  # Resume only an explicitly started durable schedule.
            try:
                yield
            finally:
                if task:
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
        finally:
            if engine:
                await run_in_threadpool(engine.close)
            lock.close()

    app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost", "testserver"])

    @app.middleware("http")
    async def local_boundary(request, call_next):
        if profile == 'local' and (not request.client or request.client.host not in ('127.0.0.1', '::1', 'testclient')):
            return JSONResponse({'error': 'loopback_required'}, 403, headers={'Cache-Control': 'no-store'})
        if registry and (request.url.path == '/api' or request.url.path.startswith('/api/')):
            try:
                request.state.principal = registry.authenticate(request.headers.get('authorization'))
                await app.state.access.authorize(request, request.state.principal)
            except WorkflowError as error:
                try:
                    app.state.access.audit(getattr(request.state, 'principal', None), request.method, error.status)
                except Exception:
                    pass  # Preserve denial even when its private audit store is unavailable.
                return JSONResponse({'error': error.code}, error.status, headers={'Cache-Control': 'no-store'})
            except Exception:
                return JSONResponse({'error': 'access_denied'}, 403, headers={'Cache-Control': 'no-store'})
        if request.method not in ("GET", "HEAD"):
            if request.headers.get("origin") is not None and request.headers.get("origin") not in origins:
                return JSONResponse({"error": "origin_not_allowed"}, 403, headers={'Cache-Control': 'no-store'})
            if not registry and request.headers.get("x-faulttrace-local") != "1":
                return JSONResponse({"error": "local_client_header_required"}, 403, headers={'Cache-Control': 'no-store'})
        try:
            response = await call_next(request)
        except Exception:
            response = JSONResponse({"error": "storage_or_internal_failure"}, 500)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        if registry and hasattr(request.state, 'principal'):
            try:
                app.state.access.audit(request.state.principal, request.method, response.status_code)
            except Exception:
                return JSONResponse({'error': 'storage_or_internal_failure'}, 500,
                                    headers={'Cache-Control': 'no-store'})
        return response

    @app.exception_handler(WorkflowError)
    async def workflow_error(request, error):
        return JSONResponse({"error": error.code}, error.status)

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request, error):
        return JSONResponse({"error": "invalid_request"}, 400)

    @app.get("/api/state")
    def state(request: Request):
        with app.state.workflow.write_lock:
            snapshot = app.state.workflow.store.snapshot()
            result = dict(snapshot, test_output=test_output, photo_planning={'version': 1}, photo_analysis={'version': 1, 'contract': 'photo-observation-v1'}, photo_collection={'version': 1, 'assets': ['F-17', 'V-08']}, journey=app.state.journey.snapshot(), inference_enabled=inference_enabled,
                        mode="local server / simulated incident / real inference only on explicit action")
            if result['journey']:
                result['journey']['monitoring'] = app.state.monitor.snapshot()
            if hasattr(app.state, 'documentation'):
                result['documentation'] = {'enabled': bool(app.state.documentation.enabled)}
            return app.state.access.scope(request.state.principal, result) if registry else result

    @app.get('/api/identity')
    def identity(request: Request):
        p = request.state.principal if registry else {}
        return {'profile': profile, 'principal_id': p.get('principal_id'), 'role': p.get('role'),
                'capabilities': {'create_incident': p.get('create', False)},
                'incident_ids': p.get('incidents', [])}

    def start_authorized(request, operation, *args):
        with app.state.workflow.write_lock:
            if registry:
                # Admission may predate a concurrent creator grant or a later
                # administrator removal. Reauthenticate at the serialized boundary.
                principal = registry.authenticate(request.headers.get('authorization'))
                request.state.principal = principal
                if principal['role'] != 'commander' or not principal['create']:
                    raise WorkflowError('access_denied', 403)
                with app.state.workflow.store.connection() as db:
                    existing = db.execute('SELECT id FROM incidents').fetchone()
                if existing:
                    app.state.access.incident(principal)
            incident_id = operation(*args)
            if registry and not existing:
                registry.grant_creator(principal['principal_id'], incident_id)
            return incident_id

    def key(request):
        return identifier(request.headers.get("idempotency-key"))

    @app.post("/api/incidents")
    async def start(request: Request):
        await fields(request, [])
        incident_id = await run_in_threadpool(start_authorized, request, app.state.workflow.start, key(request))
        return {"incident_id": incident_id}

    @app.post('/api/investigations')
    async def investigation_start(request: Request):
        await fields(request, [])
        result = await run_in_threadpool(start_authorized, request, app.state.journey.start, key(request), True)
        return {'incident_id': result}

    @app.post('/api/tasks/{task_id}/observations')
    async def independent_observation(task_id: str, request: Request):
        from .human_observations import submit
        body = await fields(request, ['revision', 'task_revision', 'photo_id', 'decision',
            'observed_asset_id', 'measurement_type', 'reading', 'unit', 'position', 'independent'])
        result = await run_in_threadpool(submit, app.state.journey, task_id, body, key(request))
        return {'evidence_id': result}

    @app.post('/api/simulation/start')
    async def simulation_start(request: Request):
        await fields(request, [])
        result = await run_in_threadpool(start_authorized, request, app.state.journey.start, key(request))
        return {'incident_id': result}

    @app.post('/api/simulation/advance')
    async def simulation_advance(request: Request):
        body = await fields(request, ['revision'])
        result = await run_in_threadpool(app.state.journey.advance, body['revision'], key(request))
        return {'tick': result}

    @app.post('/api/simulation/monitor')
    async def simulation_monitor(request: Request):
        body = await fields(request, ['revision'])
        target = await run_in_threadpool(app.state.monitor.start, body['revision'], key(request))
        app.state.start_monitor()
        return {'target_tick': target}

    @app.post('/api/tasks/{task_id}/renew-observation')
    async def renew_observation(task_id: str, request: Request):
        from .walkthrough import renew
        body = await fields(request, ['revision'])
        result = await run_in_threadpool(renew, app.state.journey, task_id, body['revision'], key(request))
        return {'task_id': result}

    @app.post('/api/simulation/observe')
    async def simulation_observe(request: Request):
        body = await fields(request, ['revision', 'asset_id', 'status', 'reading'])
        result = await run_in_threadpool(app.state.journey.observe, body['revision'], body['asset_id'],
                                         body['status'], body['reading'], key(request))
        return {'evidence_id': result}

    @app.post('/api/simulation/approve')
    async def simulation_approve(request: Request):
        body = await fields(request, ['revision', 'action_id', 'decision'])
        result = await run_in_threadpool(app.state.journey.approve, body['revision'], body['action_id'], body['decision'], key(request))
        return {'approval_id': result}

    @app.post('/api/simulation/execute')
    async def simulation_execute(request: Request):
        body = await fields(request, ['revision', 'approval_id'])
        if registry:
            app.state.access.correction(request.state.principal, body['approval_id'])
        result = await run_in_threadpool(app.state.journey.execute, body['revision'], body['approval_id'], key(request))
        return {'execution_id': result}

    @app.post("/api/tasks/{task_id}/images")
    async def image(task_id: str, request: Request):
        try:
            revision = int(request.headers.get("x-task-revision", ""))
        except ValueError:
            raise WorkflowError("invalid_revision", 400) from None
        purpose = request.headers.get('x-evidence-purpose')
        if purpose not in (None, 'reference-photo'):
            raise WorkflowError('invalid_evidence_purpose', 400)
        if purpose and request.headers.get('x-fixture-id') is not None:
            raise WorkflowError('invalid_evidence_purpose', 400)
        body = await bounded_body(request, MAX_UPLOAD)
        image = await run_in_threadpool(validate_upload, body, request.headers.get("content-type"),
                                       request.headers.get("x-fixture-id"))
        evidence_id = await run_in_threadpool(app.state.workflow.submit, task_id, revision, key(request), image=image, reference_photo=purpose == 'reference-photo')
        return {"evidence_id": evidence_id}

    @app.post('/api/planning', status_code=202)
    async def plan(request: Request):
        body = await fields(request, ['revision'])
        attempt_id = await run_in_threadpool(app.state.engine.planner.choose, body['revision'], key(request))
        return {'attempt_id': attempt_id}

    @app.post('/api/tasks/{task_id}/photo-follow-up')
    async def photo_follow_up(task_id: str, request: Request):
        from .photo_planning import forward_for_planning
        body = await fields(request, ['revision', 'evidence_id'])
        eid = await run_in_threadpool(forward_for_planning, app.state.workflow,
                                     task_id, body['revision'], body['evidence_id'], key(request))
        return {'evidence_id': eid}

    @app.post("/api/tasks/{task_id}/reports")
    async def report(task_id: str, request: Request):
        body = await fields(request, ["revision", "report"])
        evidence_id = await run_in_threadpool(app.state.workflow.submit, task_id, body["revision"],
                                             key(request), report=body["report"])
        return {"evidence_id": evidence_id}

    @app.post("/api/tasks/{task_id}/reopen")
    async def reopen(task_id: str, request: Request):
        body = await fields(request, ["revision"])
        await run_in_threadpool(app.state.workflow.reopen, task_id, body["revision"], key(request))
        return {"task_id": task_id}

    @app.post("/api/evidence/{evidence_id}/analyze", status_code=202)
    async def analyze(evidence_id: str, request: Request):
        body = await fields(request, ["revision"])
        analysis_id = await run_in_threadpool(app.state.engine.analyze, evidence_id, body["revision"], key(request))
        return {"analysis_id": analysis_id}

    @app.post('/api/evidence/{evidence_id}/analyze-photo', status_code=202)
    async def analyze_photo(evidence_id: str, request: Request):
        body = await fields(request, ['revision'])
        analysis_id = await run_in_threadpool(app.state.engine.photos.analyze, evidence_id, body['revision'], key(request))
        return {'analysis_id': analysis_id}

    @app.get("/api/evidence/{evidence_id}/image")
    def image_content(evidence_id: str):
        evidence_id = identifier(evidence_id)
        with app.state.workflow.store.connection() as db:
            found = db.execute("SELECT id FROM evidence WHERE id=? AND kind='image'", (evidence_id,)).fetchone()
        path = app.state.workflow.store.images / (evidence_id + ".png")
        if not found or not path.is_file():
            raise WorkflowError("evidence_not_found", 404)
        return FileResponse(path, media_type="image/png")

    if documentation_options is not None:
        from .documentation import register
        register(app, **documentation_options)
    return app
