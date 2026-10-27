"""Photographic claims for observation planning only; no recovery-policy imports."""
import json
import re
from datetime import datetime, timezone

PHOTO_MAX_AGE_SECONDS = 1800  # Planning freshness only; not correction policy.

from faulttrace.photo_observation import validate_photo_observation
from faulttrace.validation import ProbeError
from .storage import WorkflowError, identifier


def assessments(db):
    rows = list(db.execute('''SELECT e.*,t.asset_id,t.capability,a.id AS analysis_id,
        a.status AS analysis_status,a.interpretation,a.receipt,p.contract
        FROM evidence e JOIN tasks t ON t.id=e.task_id
        LEFT JOIN analyses a ON a.evidence_id=e.id
        LEFT JOIN photo_analyses p ON p.analysis_id=a.id
        WHERE e.kind='image' AND e.origin='user-upload' AND e.fixture_id IS NULL
        ORDER BY e.rowid'''))
    latest = {r['task_id']: r['id'] for r in rows}
    humans = [dict(r) for r in db.execute("SELECT id,task_id,report FROM evidence WHERE kind='report' AND origin='human-report'")]
    # Explicitly public human observations, never sim_runs / hidden outcomes.
    from .investigation_evidence import observations
    numeric = [r for r in observations(db, policy=True) if r['status'] == 'readable']
    results = []
    factors = {'pa': .001, 'kpa': 1, 'mpa': 1000, 'bar': 100, 'mbar': .1, 'psi': 6.894757293}
    for row in rows:
        ref = 'evidence-' + row['id']
        flags, conflicts, claim = ['identity_unconfirmed'], [], None
        identity, compatible = 'unknown', False
        if row['analysis_status'] == 'interpreted' and row['contract'] == 'photo-observation-v1':
            try:
                value = json.loads(row['interpretation'])
                receipt = json.loads(row['receipt'])
                if receipt.get('validation_result') != 'passed':
                    raise ValueError()
                # Recheck the stored contract, but never send free-form label text.
                value = validate_photo_observation({'choices': [{'finish_reason': 'stop',
                    'message': {'role': 'assistant', 'content': json.dumps(value)}}]}, ref)
                claim = {k: value[k] for k in ('category', 'readability', 'measurement_type',
                    'reading', 'visible_unit', 'valve_orientation', 'reasons')}
                tag = value['label_text']
                if tag and re.fullmatch(r'[A-Z]{1,3}-[0-9]{1,4}', tag) and tag != row['asset_id']:
                    identity = 'model_tag_mismatch'
                    flags.append('model_tag_disagrees_with_assignment')
                if value['readability'] != 'readable' or value['reading'] is None:
                    flags.append('reading_not_established')
                if row['capability'] == 'READ_LOCAL_DP':
                    compatible = value['category'] == 'gauge' and value['measurement_type'] == 'differential_pressure'
                    if value['measurement_type'] == 'pressure':
                        flags.append('pressure_is_not_differential_pressure')
                    elif not compatible:
                        flags.append('measurement_type_unresolved')
                else:
                    flags.append('handle_orientation_does_not_verify_position')
                if value['reasons']:
                    flags.append('model_reports_uncertainty')
            except (ValueError, TypeError, KeyError, ProbeError):
                flags.append('validated_interpretation_unavailable')
        else:
            flags.append('validated_interpretation_unavailable')
        reports = [h for h in humans if h['task_id'] == row['task_id']]
        from .investigation_evidence import details
        for report in reports:
            human = details(db, report['id'])
            if human and human['photo_id'] == row['id'] and human['flags']:
                conflicts.append('evidence-' + report['id'])
                flags.append('human_model_report_disagreement')
        if any(h['report'] == 'wrong-equipment' for h in reports):
            identity = 'human_reported_wrong_equipment'
            flags.append('human_reports_wrong_equipment')
        if claim and claim['readability'] == 'readable' and any(h['report'] == 'unreadable' for h in reports):
            conflicts += ['evidence-' + h['id'] for h in reports if h['report'] == 'unreadable']
            flags.append('human_model_readability_disagreement')
        if claim and compatible and claim['reading'] is not None:
            unit = (claim['visible_unit'] or '').casefold()
            for h in numeric:
                other = (h['unit'] or '').casefold()
                if h['asset_id'] == row['asset_id'] and unit in factors and other in factors:
                    # Numeric equality only (1e-6 kPa rounding tolerance), not an operating band.
                    if abs(claim['reading'] * factors[unit] - h['reading'] * factors[other]) > 1e-6:
                        conflicts.append(h['id'])
                        flags.append('human_model_numeric_disagreement')
        try:
            age = (datetime.now(timezone.utc) - datetime.fromisoformat(row['created_at'])).total_seconds()
            expired = not 0 <= age <= PHOTO_MAX_AGE_SECONDS
        except (ValueError, TypeError):
            expired = True
        stale = expired or row['status'] == 'stale' or row['analysis_status'] == 'stale' or latest[row['task_id']] != row['id']
        status = 'unresolved'
        if stale:
            status = 'stale'; flags.append('stale_or_superseded')
        elif conflicts:
            status = 'disputed'
        elif identity != 'unknown' or (claim and claim['measurement_type'] in ('pressure', 'unsupported')):
            status = 'incompatible'
        elif claim and compatible and claim['readability'] == 'readable' and claim['reading'] is not None and not claim['reasons']:
            status = 'usable'
        results.append({'evidence_id': row['id'], 'evidence_ref': ref, 'task_id': row['task_id'],
            'assigned_asset': row['asset_id'], 'required_capability': row['capability'],
            'source': row['origin'], 'analysis_id': row['analysis_id'], 'analysis_status': row['analysis_status'],
            'timestamp': row['created_at'], 'status': status, 'identity_status': identity,
            'measurement_compatible_claim': compatible, 'claim': claim,
            'flags': list(dict.fromkeys(flags)), 'conflicting_refs': list(dict.fromkeys(conflicts)),
            'model_claim_only': True, 'satisfies_measurement_requirement': False,
            'requires_clarification': True})
    return results


def context_photo(item):
    return {'evidence_ref': item['evidence_ref'], 'evidence_id': item['evidence_id'],
        'task_id': item['task_id'], 'asset_id': item['assigned_asset'], 'kind': 'photographic_claim',
        'origin': item['source'], 'status': item['status'], 'report': None,
        'interpretation': None, 'photographic_observation': item}


def forward_for_planning(workflow, task_id, revision, evidence_id, key):
    """Explicit handoff releases the blocker, never completes a measurement task."""
    with workflow.write_lock, workflow.store.connection(write=True) as db:
        fingerprint, existing = workflow.store.operation(db, key, 'photo-follow-up', [task_id, revision, evidence_id])
        if existing:
            return existing
        task = workflow.store.task(db, task_id, revision)
        identifier(evidence_id)
        latest = db.execute('SELECT id FROM tasks ORDER BY rowid DESC LIMIT 1').fetchone()
        item = next((p for p in assessments(db) if p['evidence_id'] == evidence_id and p['task_id'] == task_id), None)
        if (not item or latest['id'] != task_id or task['status'] != 'awaiting'
                or item['analysis_status'] != 'interpreted' or item['claim'] is None or item['status'] == 'stale'):
            raise WorkflowError('photo_follow_up_unavailable', 409)
        db.execute("UPDATE tasks SET revision=revision+1,status='needs_evidence' WHERE id=?", (task_id,))
        workflow.store.event(db, 'photo_sent_for_follow_up_planning', evidence_id)
        workflow.store.remember(db, key, fingerprint, evidence_id)
        return evidence_id
