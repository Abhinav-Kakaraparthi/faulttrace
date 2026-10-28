"""Per-run production workflow, with internal role grants and no model transport."""
import secrets
import sqlite3
from contextlib import closing
import uuid

from .storage import WorkflowError, now


class DemoRegistry:
    """Trusted in-process adapter, never a browser credential issuer."""
    def __init__(self, directory):
        self.directory = directory
        self.tokens = {role: secrets.token_urlsafe(32) for role in ('commander', 'operator')}

    def read(self):
        with closing(sqlite3.connect((self.directory / 'workflow.sqlite3').as_uri() + '?mode=ro', uri=True)) as db:
            incident = db.execute('SELECT id FROM incidents').fetchone()
        grants = [incident[0]] if incident else []
        principals = {role: {'principal_id': 'demo-' + role, 'role': role,
                            'create': False, 'incidents': grants} for role in self.tokens}
        return {'principals': principals, 'operators': {i: 'demo-operator' for i in grants}}

    def authenticate(self, header):
        for role, token in self.tokens.items():
            if isinstance(header, str) and secrets.compare_digest(header, 'Bearer ' + token):
                return self.read()['principals'][role]
        raise WorkflowError('authentication_required', 401)


def forbidden_transport(*args):
    raise RuntimeError('demo_inference_forbidden')


def assign(app, action, revision, key):
    """Explicit application-template assignment, never a mocked model proposal."""
    from .planner_contract import build_context, permitted_actions
    workflow, store = app.state.workflow, app.state.workflow.store
    with workflow.write_lock, store.connection(write=True) as db:
        fingerprint, duplicate = store.operation(db, key, 'demo_assignment', [action, revision])
        if duplicate:
            return duplicate
        app.state.journey.revision(db, revision)
        if app.state.journey.run(db)['executed_tick'] is not None:
            raise WorkflowError('simulation_observations_closed', 409)
        if app.state.journey.blocking(db):
            raise WorkflowError('active_task_conflict', 409)
        if db.execute("SELECT COUNT(*) FROM events WHERE kind='demo_template_assigned'").fetchone()[0] >= 4:
            raise WorkflowError('demo_assignment_budget', 409)
        context = build_context(db)
        if type(action) is not str or action not in permitted_actions(context):
            raise WorkflowError('demo_action_unavailable', 409)
        kind, asset, capability = permitted_actions(context)[action]
        result = str(uuid.uuid4())
        if kind == 'ESCALATE':
            store.event(db, 'demo_human_escalation_requested')
        else:
            incident = db.execute('SELECT id FROM incidents').fetchone()[0]
            db.execute('''INSERT INTO tasks(id,incident_id,revision,status,created_at,asset_id,
                capability,creation_source,explanation) VALUES(?,?,1,'awaiting',?,?,?,
                'Demo application template / not NVIDIA-generated',
                'Application-assigned simulated observation. No model request or equipment action.')''',
                       (result, incident, now(), asset, capability))
        store.event(db, 'demo_template_assigned')
        store.remember(db, key, fingerprint, result)
        return result


async def open_run(stack, directory, origin):
    from .api import create_app
    registry = DemoRegistry(directory / 'data')
    app = create_app(directory / 'data', directory / 'usage.json', enabled=False,
                     key_source=lambda: None, send=forbidden_transport,
                     profile='demo', demo_registry=registry, browser_origin=origin)
    await stack.enter_async_context(app.router.lifespan_context(app))
    workflow = app.state.workflow
    with workflow.store.connection() as db:
        exists = db.execute('SELECT 1 FROM incidents').fetchone()
    if not exists:
        app.state.journey.start(str(uuid.uuid4()), True)
        assign(app, 'OBSERVE_F-17_READ_LOCAL_DP', 1, str(uuid.uuid4()))
    return app, registry
