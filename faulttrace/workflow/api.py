"""Loopback-only local API; raw uploads and logs never include the provider key."""
from contextlib import asynccontextmanager
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
               enabled=None, key_source=None, simulation_clock=None, simulation_outcome="effective"):
    origins = allowed_origins()
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
            engine = AnalysisEngine(workflow, ledger_path, send, inference_enabled, revision=source_revision(), **kwargs)
            app.state.workflow, app.state.engine = workflow, engine
            app.state.journey = Journey(workflow, simulation_clock, simulation_outcome)
            yield
        finally:
            if engine:
                await run_in_threadpool(engine.close)
            lock.close()

    app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost", "testserver"])

    @app.middleware("http")
    async def local_boundary(request, call_next):
        if request.method not in ("GET", "HEAD"):
            if request.headers.get("origin") is not None and request.headers.get("origin") not in origins:
                return JSONResponse({"error": "origin_not_allowed"}, 403)
            if request.headers.get("x-faulttrace-local") != "1":
                return JSONResponse({"error": "local_client_header_required"}, 403)
        try:
            response = await call_next(request)
        except Exception:
            response = JSONResponse({"error": "storage_or_internal_failure"}, 500)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    @app.exception_handler(WorkflowError)
    async def workflow_error(request, error):
        return JSONResponse({"error": error.code}, error.status)

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request, error):
        return JSONResponse({"error": "invalid_request"}, 400)

    @app.get("/api/state")
    def state():
        with app.state.workflow.write_lock:
            snapshot = app.state.workflow.store.snapshot()
            return dict(snapshot, photo_analysis={'version': 1, 'contract': 'photo-observation-v1'}, photo_collection={'version': 1, 'assets': ['F-17', 'V-08']}, journey=app.state.journey.snapshot(), inference_enabled=inference_enabled,
                        mode="local server / simulated incident / real inference only on explicit action")

    def key(request):
        return identifier(request.headers.get("idempotency-key"))

    @app.post("/api/incidents")
    async def start(request: Request):
        await fields(request, [])
        incident_id = await run_in_threadpool(app.state.workflow.start, key(request))
        return {"incident_id": incident_id}

    @app.post('/api/simulation/start')
    async def simulation_start(request: Request):
        await fields(request, [])
        result = await run_in_threadpool(app.state.journey.start, key(request))
        return {'incident_id': result}

    @app.post('/api/simulation/advance')
    async def simulation_advance(request: Request):
        body = await fields(request, ['revision'])
        result = await run_in_threadpool(app.state.journey.advance, body['revision'], key(request))
        return {'tick': result}

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

    return app
