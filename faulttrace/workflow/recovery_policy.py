"""Independent measurement policy. Numbers are synthetic fixture constraints only."""
from .simulation import STEP_SECONDS

POLICY = {'freshness_seconds': 120, 'pressure_agreement_kpa': 8,
          'restriction_pressure_kpa': [170, 195], 'restricted_flow_m3h': [80, 95],
          'recovery_pressure_kpa': [25, 40], 'recovery_flow_m3h': [115, 125],
          'valve_feedback_percent': [65, 80], 'window_seconds': 40, 'minimum_samples': 5}


def within(value, band):
    return band[0] <= value <= band[1]


def assess(db, run, wall_time=None):
    samples = list(db.execute('SELECT * FROM sim_samples ORDER BY tick'))
    from .investigation_evidence import observations as records, extra_blockers
    observations = records(db, policy=True)
    latest = samples[-1] if samples else None
    blockers = extra_blockers(db, wall_time, POLICY['freshness_seconds'])
    refs = [latest['id']] if latest else []
    if not latest or (run['tick'] - latest['tick']) * STEP_SECONDS > POLICY['freshness_seconds']:
        blockers.append('telemetry_missing_or_stale')
    by_asset = {asset: [o for o in observations if o['asset_id'] == asset] for asset in ('F-17', 'V-08')}
    for asset, rows in by_asset.items():
        if not rows:
            blockers.append(asset + '_missing')
            continue
        refs.extend(o['id'] for o in rows)
        if any(o['status'] in ('unreadable', 'cannot-access', 'wrong-equipment', 'cannot determine') for o in rows):
            blockers.append(asset + '_unresolved_observation')
        if (run['tick'] - rows[-1]['tick']) * STEP_SECONDS > POLICY['freshness_seconds']:
            blockers.append(asset + '_stale')
        if any(o['origin'] != 'simulated-human-report' for o in rows):
            blockers.append(asset + '_provenance_invalid')
    pressure = by_asset['F-17']
    positions = by_asset['V-08']
    readings = [o['reading'] for o in pressure if o['reading'] is not None]
    if readings and latest:
        if max(readings) - min(readings) > POLICY['pressure_agreement_kpa']:
            blockers.append('pressure_reports_conflict')
        if (abs(readings[-1] - latest['pressure']) > POLICY['pressure_agreement_kpa']
                or not within(readings[-1], POLICY['restriction_pressure_kpa'])):
            blockers.append('pressure_not_corroborated')
    if pressure and not readings:
        blockers.append('pressure_unknown')
    if positions and (len({o['status'] for o in positions}) > 1 or positions[-1]['status'] != 'intermediate'):
        blockers.append('valve_position_not_corroborated')
    if latest and (not within(latest['flow'], POLICY['restricted_flow_m3h'])
                   or not within(latest['valve'], POLICY['valve_feedback_percent'])):
        blockers.append('telemetry_not_corroborated')
    return {'source': 'deterministic fixture evidence assessment; not model output',
            'working_diagnosis': 'Evidence supports excess resistance across F-17; cause remains provisional.' if not blockers else None,
            'evidence_refs': refs, 'blockers': blockers, 'eligible': not blockers,
            'alternatives': ['Sensor discrepancy: compare local and simulated pressure.',
                             'Valve mismatch: compare human position report with simulated feedback.',
                             'Other flow restriction remains possible; recovery does not prove root cause.']}


def verify(samples, executed_tick, current_tick):
    """Only fresh post-execution samples count; no action outcome is an input."""
    if executed_tick is None:
        return {'status': 'not_started', 'sample_count': 0, 'window_seconds': 0, 'sample_refs': []}
    post = [s for s in samples if s['tick'] > executed_tick]
    good = lambda s: (within(s['flow'], POLICY['recovery_flow_m3h'])
                      and within(s['pressure'], POLICY['recovery_pressure_kpa'])
                      and within(s['valve'], POLICY['valve_feedback_percent']) and s['alarm'] is None)
    span = (post[-1]['tick'] - post[0]['tick']) * STEP_SECONDS if post else 0
    status = 'observing'
    if any(not good(s) for s in post):
        status = 'failed'
    elif post and (current_tick - post[-1]['tick']) * STEP_SECONDS > POLICY['freshness_seconds']:
        status = 'failed'
    elif any(b['tick'] - a['tick'] != 1 for a, b in zip(post, post[1:])):
        status = 'failed'
    elif len(post) >= POLICY['minimum_samples'] and span >= POLICY['window_seconds']:
        status = 'verified'
    return {'status': status, 'sample_count': len(post), 'window_seconds': span,
            'sample_refs': [s['id'] for s in post]}
