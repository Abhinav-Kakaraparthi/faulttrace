"""Independent offline cases distinguish provider emptiness from URL filtering."""
import json
from pathlib import Path
import tempfile
import unittest
import uuid

from fastapi.testclient import TestClient
from faulttrace.partners.http import PartnerError
from faulttrace.partners.tavily import context,parse,payload
from faulttrace.workflow.api import create_app
from faulttrace.workflow.documentation import register
from test_partners import Budget

SECRET='SENTINEL_SOURCE_DIAGNOSTICS_KEY'
CTX=context('WIKA','A-10','wika.com')


def item(url,title='A-10 data sheet'):
    return {'url':url,'title':title,'content':'OFFLINE reference; not equipment evidence.'}


def envelope(rows,**changes):
    return json.dumps(dict(results=rows,usage={'credits':1},**changes)).encode()


class TavilySourceDiagnosticsTests(unittest.TestCase):
    def test_exact_request_unchanged_and_domain_restriction_is_explicit(self):
        self.assertEqual(payload(CTX),{'query':'WIKA "A-10" manufacturer manual datasheet',
            'topic':'general','search_depth':'basic','max_results':3,'include_domains':['wika.com'],
            'include_domains_mode':'restrict','include_answer':False,'include_raw_content':False,
            'include_images':False,'auto_parameters':False,'include_usage':True})

    def test_provider_empty_results_are_explicit_without_inventing_sources(self):
        result=parse(envelope([]),CTX,SECRET)
        self.assertEqual(result['sources'],[]);self.assertEqual(result['usage_credits'],1)
        self.assertEqual(result['source_diagnostics'],{'returned_count':0,'examined_count':0,
            'retained_count':0,'filtered_count':0,'not_examined_count':0,'filter_reasons':{},
            'outcome':'provider_results_empty'})

    def test_nonempty_all_filtered_results_are_distinct_and_reason_counts_safe(self):
        rows=[item(url) for url in ('https://wika.com.evil.invalid/x','http://www.wika.com/a',
            'https://user@wika.com/a','https://wika.com:9443/a','https://wika.com/x?key='+SECRET,
            'https://wika.com/'+('x'*520),'https://wika.com/a\nb')]
        result=parse(envelope(rows),CTX,SECRET);d=result['source_diagnostics']
        self.assertEqual(result['sources'],[]);self.assertEqual(result['usage_credits'],1)
        self.assertEqual(d['returned_count'],7);self.assertEqual(d['filtered_count'],7)
        self.assertEqual(d['examined_count'],7);self.assertEqual(d['not_examined_count'],0)
        self.assertEqual(d['outcome'],'all_examined_results_filtered')
        self.assertEqual(d['filter_reasons'],{'outside_official_domain':1,'non_https':1,
            'url_credentials':1,'unsupported_port':1,'credential_in_url':1,
            'url_too_long':1,'url_control_characters':1})
        self.assertNotIn(SECRET,json.dumps(result));self.assertNotIn('evil.invalid',json.dumps(result))

    def test_apex_www_and_other_official_subdomain_retained_even_without_model_text(self):
        rows=[item(url,'Unrelated title') for url in ('https://wika.com/a','https://www.wika.com/a',
                                                     'https://shop.wika.com/a')]
        result=parse(envelope(rows),CTX,SECRET)
        self.assertEqual([s['url'] for s in result['sources']],[r['url'] for r in rows])
        self.assertEqual([s['model_match'] for s in result['sources']],['unverified']*3)
        self.assertEqual(result['source_diagnostics']['filtered_count'],0)

    def test_citation_cap_is_not_counted_as_domain_rejection(self):
        rows=[item('https://outside.invalid/x')]+[item('https://www.wika.com/'+str(i)) for i in range(4)]
        d=parse(envelope(rows),CTX,SECRET)['source_diagnostics']
        self.assertEqual(d,{'returned_count':5,'examined_count':4,'retained_count':3,
            'filtered_count':1,'not_examined_count':1,'filter_reasons':{'outside_official_domain':1},
            'outcome':'sources_retained'})

    def test_malformed_envelopes_and_items_still_fail_closed(self):
        for body in (b'{}',b'{"results":{},"usage":{"credits":1}}',b'{"results":[],"results":[]}',
                     envelope([{'url':42}]),envelope([item('https://wika.com:invalid/x')]),
                     envelope([{'url':'https://wika.com/x','title':False,'content':'text'}])):
            with self.subTest(body_size=len(body)),self.assertRaises(PartnerError) as caught:
                parse(body,CTX,SECRET)
            self.assertEqual(caught.exception.code,'documentation_response_invalid')

    def test_production_route_persists_counts_without_turning_references_into_evidence(self):
        for rows,outcome in (([],'provider_results_empty'),([item('https://outside.invalid/x')],'all_examined_results_filtered')):
            with self.subTest(outcome=outcome),tempfile.TemporaryDirectory() as directory:
                root=Path(directory);app=create_app(root/'data',root/'usage.json',enabled=False)
                budget=Budget();calls=[]
                def send(key,request):calls.append(request);return envelope(rows)
                register(app,enabled=True,key_source=lambda:SECRET,send=send,budget=budget)
                with TestClient(app) as client:
                    headers={'X-FaultTrace-Local':'1','Idempotency-Key':str(uuid.uuid4())}
                    client.post('/api/investigations',json={},headers=headers)
                    before=client.get('/api/state').json()
                    headers['Idempotency-Key']=str(uuid.uuid4())
                    response=client.post('/api/documentation',json=dict(CTX,revision=before['incident']['revision']),headers=headers)
                    self.assertEqual(response.status_code,200)
                    record=client.get('/api/documentation').json()['records'][0]
                    self.assertEqual(record['result']['source_diagnostics']['outcome'],outcome)
                    self.assertEqual(record['receipt']['usage_credits'],1)
                    self.assertEqual(record['result']['sources'],[])
                    after=client.get('/api/state').json()
                    self.assertEqual(before['evidence'],after['evidence'])
                    self.assertEqual(before['journey']['assessment'],after['journey']['assessment'])
                    self.assertEqual(len(calls),1);self.assertEqual(len(budget.receipts),1)

    def test_legacy_result_without_counts_is_preserved_not_backfilled(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);app=create_app(root/'data',root/'usage.json',enabled=False)
            service=register(app,enabled=False,budget=Budget())
            with TestClient(app):
                service.initialize()
                old={'sources':[],'usage_credits':1,'retrieved_at':'2026-10-29T15:31:12+00:00'}
                with service.workflow.store.connection(write=True) as db:
                    db.execute("INSERT INTO documentation(id,status,context,result) VALUES(?,'completed',?,?)",
                               (str(uuid.uuid4()),json.dumps(CTX),json.dumps(old)))
                result=service.records()['records'][0]['result']
                self.assertEqual(result,old);self.assertNotIn('source_diagnostics',result)
