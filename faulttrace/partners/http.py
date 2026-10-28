"""Single bounded HTTPS POST, no redirects, retries, headers or response logging."""
import json
import urllib.error
import urllib.request


class PartnerError(Exception):
    def __init__(self, code):
        self.code = code


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def post_json(url, headers, payload, *, timeout=8, limit=131072):
    request = urllib.request.Request(url, data=json.dumps(payload, allow_nan=False).encode(),
        headers=dict(headers, **{'Content-Type': 'application/json'}), method='POST')
    try:
        with urllib.request.build_opener(NoRedirect()).open(request, timeout=timeout) as response:
            body = response.read(limit + 1)
            if len(body) > limit:
                raise PartnerError('partner_response_too_large')
            return body
    except PartnerError:
        raise
    except urllib.error.HTTPError as error:
        error.close()  # Never inspect or retain provider error bodies/headers.
        raise PartnerError('partner_http_error') from None
    except Exception:
        raise PartnerError('partner_transport_error') from None
