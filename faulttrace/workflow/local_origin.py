"""Explicit loopback preview origin; never allow arbitrary browser origins."""
import os
import re

DEFAULT_ORIGINS = frozenset({
    'http://127.0.0.1:5173', 'http://localhost:5173',
    'http://127.0.0.1:5180', 'http://localhost:5180',
})


def allowed_origins():
    value = os.environ.get('FAULTTRACE_PREVIEW_ORIGIN')
    if value is None:
        return DEFAULT_ORIGINS
    match = re.fullmatch(r'http://(127\.0\.0\.1|localhost):([0-9]{1,5})', value)
    if not match or not 1 <= int(match[2]) <= 65535:
        raise ValueError('invalid_preview_origin')
    return DEFAULT_ORIGINS | {value}
