"""Opt-in, allowlisted LangSmith metadata. No auto instrumentation or body export."""
from datetime import datetime, timedelta, timezone
import os
import re
import uuid

from .http import post_json

ENDPOINT = 'https://api.smith.langchain.com/runs'
OPERATIONS = {'planning', 'photo_analysis', 'documentation'}
MODELS = {'nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B', 'nvidia/Nemotron-3.5-Super-VL'}


def metadata(operation, receipt):
    """Fresh projection; never pass a receipt/request dictionary through wholesale."""
    if operation not in OPERATIONS or type(receipt) is not dict:
        raise ValueError('invalid_trace_operation')
    result = {'operation': operation, 'correlation_id': str(uuid.uuid4())}
    latency = receipt.get('latency_ms')
    if type(latency) is int and 0 <= latency <= 3600000:
        result['latency_ms'] = latency
    model = receipt.get('returned_model') or receipt.get('requested_model')
    if model in MODELS:
        result['model'] = model
    status = receipt.get('validation_result')
    result['validation_result'] = status if status in ('passed', 'failed') else 'unknown'
    usage = receipt.get('token_usage')
    result['token_usage'] = {k: usage[k] for k in ('prompt_tokens', 'completion_tokens', 'total_tokens', 'reasoning_tokens')
        if type(usage) is dict and type(usage.get(k)) is int and 0 <= usage[k] <= 10000000}
    reasoning = receipt.get('reasoning_tokens')
    if type(reasoning) is int and 0 <= reasoning <= 10000000:
        result['reasoning_tokens'] = reasoning
    error = receipt.get('error')
    result['error_category'] = ('none' if error is None else 'provider_failure' if error in
        ('provider_http_error', 'provider_network_error', 'network_error', 'partner_http_error', 'partner_transport_error') else
        'validation_failed' if error in ('invalid_proposal', 'invalid_image_evidence', 'invalid_photo_observation',
        'non_stop_completion', 'documentation_response_invalid') else 'operation_failed')
    return result


def trace_transport(key, request):
    post_json(ENDPOINT, {'x-api-key': key}, request, timeout=3, limit=4096)


def emit_trace(operation, receipt, *, enabled=None, send=trace_transport):
    """One bounded best-effort export; fixed return status and never retries/raises."""
    try:
        active = os.environ.get('FAULTTRACE_LANGSMITH_TRACING') == '1' if enabled is None else enabled
        if not active:
            return 'disabled'
        key, project = os.environ.get('LANGSMITH_API_KEY'), os.environ.get('LANGSMITH_PROJECT')
        if not key or not project or not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', project):
            return 'unavailable'
        safe = metadata(operation, receipt)
        end = datetime.now(timezone.utc)
        start = end - timedelta(milliseconds=safe.get('latency_ms', 0))
        request = {'id': safe['correlation_id'], 'name': 'faulttrace.' + operation, 'run_type': 'chain',
            'session_name': project, 'inputs': {}, 'outputs': {}, 'extra': {'metadata': safe},
            'start_time': start.isoformat(), 'end_time': end.isoformat()}
        if key in str(request):
            return 'failed'
        send(key, request)
        return 'recorded'
    except Exception:
        return 'failed'
