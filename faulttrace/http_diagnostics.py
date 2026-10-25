"""Status-derived diagnostics only; never inspect provider bodies or headers."""
from .validation import ProbeError

HTTP_FIELDS = ('http_status', 'http_error_category')
STATUS_CATEGORIES = {
    400: 'http_bad_request', 401: 'http_unauthorized', 402: 'http_payment_required',
    403: 'http_forbidden', 404: 'http_not_found', 422: 'http_unprocessable_entity',
    429: 'http_rate_limited',
}


def category(status):
    if status is None:
        return 'http_unknown'
    if status in STATUS_CATEGORIES:
        return STATUS_CATEGORIES[status]
    if 500 <= status <= 599:
        return 'http_server_error'
    if 300 <= status <= 399:
        return 'http_redirect'
    return 'http_other_error'


class ProviderHTTPError(ProbeError):
    def __init__(self, status):
        super().__init__('provider_http_error')
        self.status = status if type(status) is int and 100 <= status <= 599 else None
        self.category = category(self.status)


def receipt_fields(value):
    """Absent legacy fields stay absent: no ledger rewrites or changed duplicates."""
    fields = {name: value[name] for name in HTTP_FIELDS if name in value}
    status, label = fields.get('http_status'), fields.get('http_error_category')
    if status is not None and (type(status) is not int or not 100 <= status <= 599):
        raise ValueError()
    if label is not None and (type(label) is not str or label != category(status)):
        raise ValueError()
    if (status is not None or label is not None) and value.get('error') != 'provider_http_error':
        raise ValueError()
    return fields
