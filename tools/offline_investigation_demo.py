"""Local test harness only: deterministic doubles, fresh ignored data, no providers.

Start with uvicorn tools.offline_investigation_demo:create_demo --factory.
This is not NVIDIA inference or evidence of model accuracy/adaptive reasoning.
"""
import base64
import hashlib
from io import BytesIO
import json
import os
from pathlib import Path
import re
import sys
import uuid

from PIL import Image
from faulttrace.accounting import MODEL, VISION_MODEL
from faulttrace.workflow.api import create_app
from tools.run_offline_tests import network_guard

ROOT = Path(__file__).resolve().parents[1]


def fake_transport(secret, payload):
    if payload['model'] == VISION_MODEL:
        ref = re.search(r'"evidence_ref":"([^"]+)"', payload['messages'][0]['content'])[1]
        data = base64.b64decode(payload['messages'][1]['content'][0]['image_url']['url'].split(',', 1)[1])
        with Image.open(BytesIO(data)) as image, Image.open(ROOT / 'fixtures/image-evidence/panel-a.png') as known:
            clear = image.size == known.size and hashlib.sha256(image.convert('RGB').tobytes()).digest() == hashlib.sha256(known.convert('RGB').tobytes()).digest()
        # Only this committed synthetic test fixture has a scripted answer.
        # Every real/unknown photograph abstains. Never use this as an evaluation.
        value = {'category': 'gauge' if clear else 'cannot-determine',
            'readability': 'readable' if clear else 'unreadable',
            'measurement_type': 'differential_pressure' if clear else 'not_applicable',
            'reading': 180 if clear else None, 'visible_unit': 'kPa' if clear else None,
            'label_text': None, 'valve_orientation': 'not_applicable',
            'reasons': [] if clear else ['category_uncertain'], 'evidence_ref': ref}
    else:
        if payload['model'] != MODEL:
            raise ValueError('offline_model_not_supported')
        context = json.loads(payload['messages'][1]['content'])
        reports = [o.get('human_observation', {}) for o in context['observations']]
        pressure = any(h.get('status') == 'readable' and not h.get('flags') for h in reports)
        valve = any(h.get('status') == 'intermediate' and not h.get('flags') for h in reports)
        blocked = context['unavailable_assets']
        action = ('OBSERVE_F-17_READ_LOCAL_DP' if not pressure and 'F-17' not in blocked
                  else 'OBSERVE_V-08_OBSERVE_POSITION' if not valve and 'V-08' not in blocked
                  else 'ESCALATE_HUMAN_INVESTIGATION')
        if any(h.get('flags') for h in reports):
            action = 'ESCALATE_HUMAN_INVESTIGATION'
        refs = [o['evidence_ref'] for o in context['observations']][-2:] or [context['telemetry']['evidence_ref']]
        value = {'action_id': action, 'context_revision': context['context_revision'],
            'evidence_refs': refs, 'explanation_code': 'human_review' if action.startswith('ESCALATE') else
            'clarify_conflict' if context['unresolved_conflicts'] else 'evidence_gap'}
    # Usage is deliberately absent: fake runs establish no actual consumption.
    return json.dumps({'id': 'chatcmpl-0000-0000', 'model': payload['model'],
        'choices': [{'finish_reason': 'stop', 'message': {'role': 'assistant', 'content': json.dumps(value)}}]}).encode()


def create_demo():
    directory = Path(os.environ.get('FAULTTRACE_DEMO_DATA_DIR',
        str(ROOT / '.local/visual' / ('unified-demo-' + uuid.uuid4().hex)))).resolve()
    if not directory.is_relative_to((ROOT / '.local').resolve()) or directory.exists():
        raise RuntimeError('offline_demo_requires_new_ignored_directory')
    # Prevent accidental Python provider access in this harness, including threads.
    sys.addaudithook(network_guard([]))
    print('OFFLINE TEST OUTPUT / scripted provider doubles / no live AI. Fresh private data: ' + str(directory))
    return create_app(directory, directory / 'test-only-usage.json', send=fake_transport,
        enabled=True, key_source=lambda: 'OFFLINE_TEST_DOUBLE', test_output=True)
