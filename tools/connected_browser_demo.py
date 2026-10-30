"""Isolated localhost browser rehearsal. Scripted doubles, never real inference.

Uses existing production API, storage, evidence policy and static SPA wrapper.
Only explicitly marked ignored test directories may be opened or resumed.
"""
import json
import os
from pathlib import Path
import sys

from faulttrace.workflow.api import create_app
from faulttrace.workflow.public_app import create_public_app
from tools.offline_investigation_demo import fake_transport
from tools.run_offline_tests import network_guard

ROOT = Path(__file__).resolve().parents[1]


def create_demo():
    root = Path(os.environ['FAULTTRACE_BROWSER_REVIEW_ROOT']).resolve()
    if not root.is_relative_to(ROOT / '.local') or root == ROOT / '.local':
        raise ValueError('isolated_review_directory_required')
    root.mkdir(parents=True, exist_ok=True)
    marker = root / 'offline-browser-review.json'
    if not marker.exists():
        if (root / 'data').exists():
            raise ValueError('unmarked_existing_data_forbidden')
        marker.write_text(json.dumps({'label': 'OFFLINE TEST OUTPUT', 'providers': 'scripted doubles',
            'fixture_identity': 'Creator-declared simulated F-17 indicator; not photographed identity verification',
            'human_inputs': 'Scripted fixture transcriptions; never NVIDIA answers or real equipment reports'}))
    elif json.loads(marker.read_text()).get('label') != 'OFFLINE TEST OUTPUT':
        raise ValueError('invalid_review_marker')
    for name in ('NEBIUS_API_KEY', 'TAVILY_API_KEY', 'LANGSMITH_API_KEY'):
        os.environ.pop(name, None)
    os.environ['FAULTTRACE_ALLOW_INFERENCE'] = '0'
    os.environ['FAULTTRACE_LANGSMITH_TRACING'] = '0'
    os.environ['FAULTTRACE_TAVILY_ENABLED'] = '0'
    blocked = []
    sys.addaudithook(network_guard(blocked))

    def send(secret, payload):
        result = fake_transport(secret, payload)
        event = {'label': 'OFFLINE TEST OUTPUT', 'model': payload['model'], 'usage': 'unknown',
                 'external_provider_calls': 0}
        if isinstance(payload['messages'][1]['content'], str):
            context = json.loads(payload['messages'][1]['content'])
            event.update(context_revision=context['context_revision'],
                         observation_refs=[o['evidence_ref'] for o in context['observations']])
        with (root / 'double-calls.jsonl').open('a', encoding='utf-8') as file:
            file.write(json.dumps(event) + '\n')
        return result

    app = create_app(root / 'data', root / 'test-only-usage.json', send=send,
                     enabled=True, key_source=lambda: 'OFFLINE_TEST_DOUBLE', test_output=True)
    return create_public_app(app, root / 'dist', os.environ['FAULTTRACE_PREVIEW_ORIGIN'])
