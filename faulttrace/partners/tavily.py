"""Restricted manufacturer-document search, not observed evidence or action policy."""
import json
import re
from urllib.parse import urlsplit

from faulttrace.validation import parse_json
from .http import PartnerError, post_json

ENDPOINT = 'https://api.tavily.com/search'
DOMAINS = {'maximator.de': 'MAXIMATOR', 'maximator.com': 'MAXIMATOR',
           'emerson.com': 'Emerson', 'wika.com': 'WIKA', 'swagelok.com': 'Swagelok'}
MODEL = re.compile(r'[A-Za-z0-9][A-Za-z0-9 ._()/+-]{0,79}\Z')


def context(manufacturer, model, domain):
    if (type(domain) is not str or domain not in DOMAINS or type(manufacturer) is not str
            or manufacturer.casefold() != DOMAINS[domain].casefold()
            or type(model) is not str or not MODEL.fullmatch(model) or model != model.strip()):
        raise PartnerError('documentation_context_invalid')
    return {'manufacturer': DOMAINS[domain], 'model': model, 'domain': domain}


def payload(value):
    return {'query': f'{value["manufacturer"]} "{value["model"]}" manufacturer manual datasheet',
            'topic': 'general', 'search_depth': 'basic', 'max_results': 3,
            'include_domains': [value['domain']], 'include_domains_mode': 'restrict',
            'include_answer': False, 'include_raw_content': False, 'include_images': False,
            'auto_parameters': False, 'include_usage': True}


def tavily_transport(key, request):
    return post_json(ENDPOINT, {'Authorization': 'Bearer ' + key}, request)


def safe_text(value, limit, secret):
    if type(value) is not str:
        raise PartnerError('documentation_response_invalid')
    value = re.sub(r'<[^>]*>', '', value)
    value = ''.join(c for c in value if c.isprintable() or c in '\n\t')
    value = value.replace(secret, '[redacted]') if secret else value
    value = re.sub(r'(?i)(?:bearer\s+|(?:tvly|lsv2|sk)-)[A-Za-z0-9_./+-]+', '[redacted]', value)
    return ' '.join(value.split())[:limit]


def parse(body, value, secret):
    try:
        if not isinstance(body, bytes) or len(body) > 131072:
            raise ValueError()
        envelope = parse_json(body.decode('utf-8'))
        if type(envelope) is not dict or type(envelope.get('results')) is not list or len(envelope['results']) > 20:
            raise ValueError()
        sources = []
        for item in envelope['results']:
            if type(item) is not dict or type(item.get('url')) is not str:
                raise ValueError()
            address = item['url']
            url = urlsplit(address)
            host = url.hostname or ''
            if (len(address) > 512 or any(ord(c) < 32 for c in address)
                    or secret and secret in address or url.scheme != 'https'
                    or url.username or url.password or url.port not in (None, 443)
                    or not (host == value['domain'] or host.endswith('.' + value['domain']))):
                continue
            # Never request URLs ourselves; citations are links, not a fetch capability.
            title = safe_text(item.get('title'), 200, secret)
            excerpt = safe_text(item.get('content'), 800, secret)
            sources.append({'url': address, 'title': title, 'excerpt': excerpt,
                'model_match': 'text_mentions_requested_model' if value['model'].casefold() in (title+' '+excerpt).casefold() else 'unverified'})
            if len(sources) == 3:
                break
        usage = envelope.get('usage')
        credits = usage.get('credits') if type(usage) is dict else None
        if type(credits) not in (int, float) or not 0 <= credits <= 1000:
            credits = None
        return {'sources': sources, 'usage_credits': credits}
    except PartnerError:
        raise
    except Exception:
        raise PartnerError('documentation_response_invalid') from None
