"""Private fixture mechanics; only timestamped measurements leave this module."""
from datetime import datetime, timezone
import uuid

STEP_SECONDS = 10


def initialize(db):
    db.executescript("""
      CREATE TABLE IF NOT EXISTS sim_runs (
        incident_id TEXT PRIMARY KEY, epoch REAL, tick INTEGER,
        private_outcome TEXT, corrected_tick INTEGER, approval_id TEXT,
        approved_revision INTEGER, approval_refs TEXT, executed_tick INTEGER);
      CREATE TABLE IF NOT EXISTS sim_samples (
        id TEXT PRIMARY KEY, tick INTEGER UNIQUE, timestamp TEXT,
        flow REAL, pressure REAL, valve REAL, alarm TEXT);
      CREATE TABLE IF NOT EXISTS sim_observations (
        id TEXT PRIMARY KEY, asset_id TEXT, status TEXT, reading REAL,
        unit TEXT, origin TEXT, timestamp TEXT, tick INTEGER);
      CREATE TABLE IF NOT EXISTS sim_approvals (
        id TEXT PRIMARY KEY, revision INTEGER, evidence_refs TEXT,
        timestamp TEXT, action_id TEXT);
    """)


def timestamp(run, tick=None):
    tick = run['tick'] if tick is None else tick
    return datetime.fromtimestamp(run['epoch'] + tick * STEP_SECONDS, timezone.utc).isoformat()


def sample(db, run):
    tick = run['tick']
    age = tick - run['corrected_tick'] if run['corrected_tick'] is not None else None
    restored = age is not None and age > 0 and run['private_outcome'] != 'ineffective'
    if run['private_outcome'] == 'relapse' and age is not None and age >= 6:
        restored = False
    flow = (120 if restored else 86) + (tick % 3 - 1)
    pressure = (32 if restored else 184) + (tick % 3 - 1) * 2
    db.execute('INSERT INTO sim_samples VALUES(?,?,?,?,?,?,?)',
               ('sample-' + str(uuid.uuid4()), tick, timestamp(run), flow, pressure, 72,
                None if restored else 'return_flow_low'))


def public_samples(db):
    return [dict(r) for r in db.execute('SELECT * FROM sim_samples ORDER BY tick')]


def planner_observations(db):
    """Explicit allowlist: no outcome, correction state, fixture labels or answer keys."""
    return [{'evidence_ref': r['id'], 'asset_id': r['asset_id'], 'kind': 'report',
             'origin': 'human-report', 'provenance': r['origin'],
             'status': 'accepted' if r['status'] in ('readable', 'intermediate', 'open', 'closed') else 'refused',
             'report': r['status'], 'timestamp': r['timestamp'],
             'interpretation': {'reading': r['reading'], 'unit': r['unit']} if r['reading'] is not None else None}
            for r in db.execute('SELECT * FROM sim_observations ORDER BY rowid')]


def augment_context(db, context):
    """Only observed, public measurements/reports enter the investigator context."""
    if not db.execute('SELECT 1 FROM sim_runs').fetchone():
        return context
    latest = db.execute('SELECT * FROM sim_samples ORDER BY tick DESC LIMIT 1').fetchone()
    reports = planner_observations(db)
    context['telemetry'] = {
        'evidence_ref': latest['id'], 'timestamp': latest['timestamp'], 'provenance': 'clock-stepped simulated telemetry',
        'return_flow': {'value': latest['flow'], 'unit': 'm3/h'},
        'differential_pressure': {'value': latest['pressure'], 'unit': 'kPa'},
        'valve_feedback': {'value': latest['valve'], 'unit': '%', 'physical_position_verified': False},
        'active_alarm': latest['alarm']}
    combined = context['observations'] + reports
    context['observations'] = combined[-16:]
    context['omitted_observations'] += max(0, len(combined) - 16)
    context['unavailable_assets'] = sorted(set(context['unavailable_assets']) | {
        r['asset_id'] for r in reports if r['report'] == 'cannot-access'})
    readings = [r['interpretation']['reading'] for r in reports if r['interpretation']]
    if readings and any(abs(r - latest['pressure']) > 8 for r in readings):
        context['unresolved_conflicts'].append('local_pressure_disagrees_with_simulated_telemetry')
    positions = {r['report'] for r in reports if r['asset_id'] == 'V-08' and r['report'] in ('open', 'intermediate', 'closed')}
    if len(positions) > 1:
        context['unresolved_conflicts'].append('human_position_reports_disagree')
    return context
