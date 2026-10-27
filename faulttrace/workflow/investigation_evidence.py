"""Canonical task evidence projections; photographic claims never become measurements."""
from datetime import datetime, timezone
import json
import re

FACTORS = {'Pa': .001, 'kPa': 1, 'MPa': 1000, 'bar': 100, 'psi': 6.894757293}


def initialize(db):
    db.executescript('''
      CREATE TABLE IF NOT EXISTS integrated_runs (incident_id TEXT PRIMARY KEY, test_output INTEGER NOT NULL DEFAULT 0);
      CREATE TABLE IF NOT EXISTS human_observations (
        evidence_id TEXT PRIMARY KEY, payload TEXT, tick INTEGER,
        timestamp TEXT, received_at TEXT);
    ''')
    if 'test_output' not in {r['name'] for r in db.execute('PRAGMA table_info(integrated_runs)')}:
        db.execute('ALTER TABLE integrated_runs ADD COLUMN test_output INTEGER NOT NULL DEFAULT 0')


def integrated(db):
    return db.execute('SELECT 1 FROM integrated_runs').fetchone() is not None


def details(db, evidence_id):
    row = db.execute('SELECT * FROM human_observations WHERE evidence_id=?', (evidence_id,)).fetchone()
    if not row:
        return None
    return dict(json.loads(row['payload']), received_at=row['received_at'],
                timestamp=row['timestamp'], tick=row['tick'], source='simulated-human-report')


def observations(db, policy=False):
    """One ID per canonical report. Legacy runs keep their original records."""
    legacy = [dict(r) for r in db.execute('SELECT * FROM sim_observations ORDER BY rowid')]
    if not integrated(db):
        return legacy
    rows = db.execute('''SELECT e.*,t.asset_id FROM evidence e JOIN tasks t ON t.id=e.task_id
        WHERE e.kind='report' ORDER BY e.rowid''')
    result = []
    for row in rows:
        human = details(db, row['id'])
        if human:
            status = human['status']
            reading = human['reading']
            unit = human['unit']
            if policy:
                reading = human['normalized_kpa']
                unit = 'kPa' if reading is not None else None
            result.append({'id': 'evidence-' + row['id'], 'evidence_id': row['id'],
                'task_id': row['task_id'], 'asset_id': row['asset_id'], 'status': status,
                'reading': reading, 'unit': unit, 'origin': 'simulated-human-report',
                'timestamp': human['timestamp'], 'tick': human['tick'], 'human_observation': human})
        else:
            # Existing refusal paths participate, but assignment-only position
            # reports cannot silently bypass independent identity confirmation.
            status = row['report'] if row['report'] in ('cannot-access', 'wrong-equipment', 'unreadable') else 'cannot determine'
            result.append({'id': 'evidence-' + row['id'], 'evidence_id': row['id'],
                'task_id': row['task_id'], 'asset_id': row['asset_id'], 'status': status,
                'reading': None, 'unit': None, 'origin': 'simulated-human-report',
                'timestamp': row['created_at'], 'tick': 0})
    return result


def photo_claim(db, photo_id, task_id):
    row = db.execute('''SELECT e.*,a.status AS analysis_status,a.interpretation,a.receipt,p.contract
        FROM evidence e LEFT JOIN analyses a ON a.evidence_id=e.id
        LEFT JOIN photo_analyses p ON p.analysis_id=a.id WHERE e.id=? AND e.task_id=?''',
        (photo_id, task_id)).fetchone()
    if not row or row['kind'] != 'image':
        return None, None
    claim = None
    if row['analysis_status'] == 'interpreted' and row['contract'] == 'photo-observation-v1':
        receipt = json.loads(row['receipt'] or '{}')
        if receipt.get('validation_result') == 'passed':
            claim = json.loads(row['interpretation'] or 'null')
    return row, claim


def review_flags(human, assigned_asset, claim):
    flags = []
    if human['observed_asset_id'] != assigned_asset:
        flags.append('observed_identity_unresolved')
    if human['decision'] == 'dispute':
        flags.append('human_disputes_photo')
    if human['decision'] == 'confirm':
        if not claim or claim['readability'] != 'readable':
            flags.append('photo_claim_unresolved')
        elif assigned_asset == 'F-17':
            tag = claim['label_text']
            if tag and re.fullmatch(r'[A-Z]{1,3}-[0-9]{1,4}', tag) and tag != human['observed_asset_id']:
                flags.append('human_model_identity_disagreement')
            if human['measurement_type'] != claim['measurement_type']:
                flags.append('human_model_type_disagreement')
            if (human['unit'] or '').casefold() != (claim['visible_unit'] or '').casefold():
                flags.append('human_model_unit_disagreement')
            if (claim['reading'] is None or human['reading'] is None
                    or abs(claim['reading'] - human['reading']) > 1e-6):
                flags.append('human_model_reading_disagreement')
        else:
            # An external handle photograph cannot confirm internal position.
            flags.append('handle_photo_not_position_verification')
    if assigned_asset == 'F-17' and human['measurement_type'] != 'differential_pressure':
        flags.append('differential_pressure_required')
    if assigned_asset == 'V-08' and (human['measurement_type'] != 'position' or human['position'] == 'cannot determine'):
        flags.append('position_unresolved')
    return flags


def extra_blockers(db, wall_time, freshness):
    """Additional guards only, never replacements for the existing fixture bands."""
    if not integrated(db):
        return []
    blockers = []
    records = observations(db)
    latest_by_asset = {o['asset_id']: o['id'] for o in records}
    reviewed = {o['human_observation']['photo_id'] for o in records if o.get('human_observation')}
    latest_photos = {r['task_id']: r['id'] for r in db.execute("SELECT id,task_id FROM evidence WHERE kind='image' ORDER BY rowid")}
    if any(photo not in reviewed for photo in latest_photos.values()):
        blockers.append('photographic_claim_requires_independent_review')
    for observation in records:
        human = observation.get('human_observation')
        if not human:
            continue
        blockers.extend(human['flags'])
        if latest_by_asset[observation['asset_id']] != observation['id']:
            continue  # Freshness follows the latest report, as in existing policy.
        if wall_time is not None:
            age = round(wall_time - datetime.fromisoformat(human['received_at']).timestamp(), 6)
            if not 0 <= age <= freshness:
                blockers.append('human_observation_wall_clock_stale')
        if human['photo_id']:
            photo, _ = photo_claim(db, human['photo_id'], observation['task_id'])
            latest = db.execute("SELECT id FROM evidence WHERE task_id=? AND kind='image' ORDER BY rowid DESC LIMIT 1",
                                (observation['task_id'],)).fetchone()
            if (not photo or photo['status'] == 'stale' or latest['id'] != human['photo_id']
                    or photo['analysis_status'] != 'interpreted'):
                blockers.append('reviewed_photo_stale')
            elif wall_time is not None:
                age = round(wall_time - datetime.fromisoformat(photo['created_at']).timestamp(), 6)
                if not 0 <= age <= freshness:
                    blockers.append('reviewed_photo_wall_clock_stale')
    return list(dict.fromkeys(blockers))
