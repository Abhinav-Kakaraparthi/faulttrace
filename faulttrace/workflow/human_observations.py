"""Explicit independent human reports, linked to tasks and optional photo claims."""
from datetime import datetime, timezone
import json
import math
import uuid

from . import investigation_evidence as evidence
from .simulation import timestamp
from .storage import WorkflowError, identifier


def submit(journey, task_id, value, key):
    fields = {'revision', 'task_revision', 'photo_id', 'decision', 'observed_asset_id',
              'measurement_type', 'reading', 'unit', 'position', 'independent'}
    if not isinstance(value, dict) or set(value) != fields:
        raise WorkflowError('invalid_human_observation')
    for name, allowed in (
        ('decision', ('independent', 'confirm', 'dispute')),
        ('observed_asset_id', ('F-17', 'V-08', 'unknown', 'other')),
        ('measurement_type', ('differential_pressure', 'pressure', 'position', 'unknown')),
    ):
        if type(value[name]) is not str or value[name] not in allowed:
            raise WorkflowError('invalid_human_observation')
    if value['independent'] is not True:
        raise WorkflowError('independent_report_required')
    reading, unit, position = (value[n] for n in ('reading', 'unit', 'position'))
    if reading is not None and (type(reading) not in (int, float) or not math.isfinite(reading) or abs(reading) > 1e9):
        raise WorkflowError('invalid_human_observation')
    if unit is not None and (type(unit) is not str or unit not in evidence.FACTORS):
        raise WorkflowError('invalid_human_observation')
    if position is not None and (type(position) is not str or position not in ('open', 'intermediate', 'closed', 'cannot determine')):
        raise WorkflowError('invalid_human_observation')
    if value['measurement_type'] in ('pressure', 'differential_pressure'):
        if reading is None or unit is None or position is not None:
            raise WorkflowError('invalid_human_observation')
    elif value['measurement_type'] == 'position':
        if reading is not None or unit is not None or position is None:
            raise WorkflowError('invalid_human_observation')
    elif reading is not None or unit is not None or position is not None:
        raise WorkflowError('invalid_human_observation')
    photo_id = value['photo_id']
    if (value['decision'] == 'independent') != (photo_id is None):
        raise WorkflowError('invalid_human_observation')
    if photo_id is not None:
        identifier(photo_id)
    workflow, store = journey.workflow, journey.store
    with workflow.write_lock, store.connection(write=True) as db:
        fingerprint, existing = store.operation(db, key, 'independent_task_observation', [task_id, value])
        if existing:
            return existing
        if not evidence.integrated(db):
            raise WorkflowError('task_investigation_required', 409)
        run = journey.run(db)
        journey.revision(db, value['revision'])
        task = store.task(db, task_id, value['task_revision'])
        if run['executed_tick'] is not None:
            raise WorkflowError('simulation_observations_closed', 409)
        latest = db.execute('SELECT id FROM tasks ORDER BY rowid DESC LIMIT 1').fetchone()
        if latest['id'] != task_id or task['status'] not in ('awaiting', 'needs_evidence', 'observed'):
            raise WorkflowError('task_not_accepting_evidence', 409)
        if db.execute('SELECT COUNT(*) FROM evidence WHERE kind=\'report\'').fetchone()[0] >= 32:
            raise WorkflowError('simulation_observation_budget_exhausted', 409)
        photo, claim = evidence.photo_claim(db, photo_id, task_id) if photo_id else (None, None)
        if photo_id and not photo:
            raise WorkflowError('evidence_not_found', 404)
        human = {k: value[k] for k in ('photo_id', 'decision', 'observed_asset_id', 'measurement_type', 'reading', 'unit', 'position')}
        flags = evidence.review_flags(human, task['asset_id'], claim)
        normalized = reading * evidence.FACTORS[unit] if value['measurement_type'] == 'differential_pressure' else None
        if task['asset_id'] == 'F-17' and (normalized is None or not 0 <= normalized <= 1000):
            flags.append('fixture_reading_incompatible')
        status = ('readable' if task['asset_id'] == 'F-17' else position) if not flags else 'unreadable'
        human.update(flags=flags, normalized_kpa=normalized if not flags else None, status=status)
        eid = str(uuid.uuid4())
        received = datetime.fromtimestamp(journey.clock(), timezone.utc).isoformat()
        db.execute('INSERT INTO evidence VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',
                   (eid, task_id, 'report', 'human-report', None, None, None, None,
                    status if not flags else 'human-dispute' if value['decision'] == 'dispute' else 'human-unresolved',
                    received, 'accepted' if not flags else 'unreadable', task['revision']))
        db.execute('INSERT INTO human_observations VALUES(?,?,?,?,?)',
                   (eid, json.dumps(human), run['tick'], timestamp(run), received))
        db.execute('UPDATE tasks SET revision=revision+1,status=? WHERE id=?',
                   ('observed' if not flags else 'needs_evidence', task_id))
        store.event(db, 'independent_human_observation_recorded', eid)
        store.remember(db, key, fingerprint, eid)
        return eid
