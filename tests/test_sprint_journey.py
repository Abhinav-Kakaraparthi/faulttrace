"""OFFLINE provider doubles: no live planning or photographic accuracy claim."""
import json
from pathlib import Path
import tempfile
import time
import unittest
import uuid

from fastapi.testclient import TestClient
from faulttrace.accounting import MODEL
from faulttrace.workflow.demo_app import create_demo_app
from faulttrace.workflow.journey import Journey, ACTION
from faulttrace.workflow.service import Workflow
from faulttrace.workflow.spending import Spending
from faulttrace.workflow.storage import Store
from faulttrace.workflow.walkthrough import RecoveryMonitor, renew
from faulttrace.workflow.human_observations import submit


def key():
    return str(uuid.uuid4())


def report(journey, asset):
    with journey.store.connection(write=True) as db:
        incident = db.execute('SELECT id FROM incidents').fetchone()[0]
        tid = key()
        capability = 'READ_LOCAL_DP' if asset == 'F-17' else 'OBSERVE_POSITION'
        db.execute("INSERT INTO tasks(id,incident_id,revision,status,created_at,asset_id,capability) VALUES(?,?,1,'awaiting','test',?,?)",
                   (tid,incident,asset,capability))
        revision = db.execute('SELECT revision FROM incidents').fetchone()[0]
    value = {'revision':revision, 'task_revision':1, 'photo_id':None,'decision':'independent',
        'observed_asset_id':asset, 'measurement_type':'differential_pressure' if asset=='F-17' else 'position',
        'reading':180 if asset=='F-17' else None,'unit':'kPa' if asset=='F-17' else None,
        'position':None if asset=='F-17' else 'intermediate','independent':True}
    return tid,submit(journey,tid,value,key())


class WalkthroughTests(unittest.TestCase):
    def setUp(self):
        self.root=Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.wall=[time.time()]

    def journey(self, name='run', demo=False, outcome='effective'):
        j=Journey(Workflow(Store(self.root/name)),lambda:self.wall[0],outcome,demo_time=demo)
        j.start(key(),True)
        if demo:
            with j.store.connection(write=True) as db:
                db.execute("INSERT INTO journey_settings VALUES(1,'paused-demo')")
        return j

    def test_paused_demo_and_non_demo_do_not_share_wall_freshness_override(self):
        demo=self.journey('demo',True)
        report(demo,'F-17')
        self.wall[0]+=600
        report(demo,'V-08')
        self.assertTrue(demo.snapshot()['assessment']['eligible'])
        release=Journey(demo.workflow,lambda:self.wall[0])
        self.assertIn('human_observation_wall_clock_stale',release.snapshot()['assessment']['blockers'])
        for _ in range(13):
            with demo.store.connection() as db:
                revision=db.execute('SELECT revision FROM incidents').fetchone()[0]
            demo.advance(revision,key())
        self.assertIn('F-17_stale',demo.snapshot()['assessment']['blockers'])

    def test_expired_report_renewal_keeps_history_and_requires_new_human_answer(self):
        j=self.journey()
        old,eid=report(j,'F-17')
        self.wall[0]+=600
        report(j,'V-08')
        with j.store.connection() as db:
            revision=db.execute('SELECT revision FROM incidents').fetchone()[0]
            original=dict(db.execute('SELECT * FROM human_observations WHERE evidence_id=?',(eid,)).fetchone())
        op=key()
        new=renew(j,old,revision,op)
        self.assertEqual(renew(j,old,revision,op),new)
        self.assertNotEqual(new,old)
        with j.store.connection() as db:
            self.assertEqual(dict(db.execute('SELECT * FROM human_observations WHERE evidence_id=?',(eid,)).fetchone()),original)
            self.assertEqual(db.execute('SELECT status FROM tasks WHERE id=?',(new,)).fetchone()[0],'awaiting')
        self.assertFalse(j.snapshot()['assessment']['eligible'])

    def test_monitor_effective_ineffective_relapse_and_restart_no_real_wait(self):
        for outcome,expected in [('effective','verified'),('ineffective','failed'),('relapse','failed')]:
            j=self.journey(outcome,True,outcome)
            report(j,'F-17'); report(j,'V-08')
            with j.store.connection() as db:
                rev=db.execute('SELECT revision FROM incidents').fetchone()[0]
            approval=j.approve(rev,ACTION,'approve',key())
            j.execute(rev,approval,key())
            self.assertEqual(j.snapshot()['recovery']['status'],'observing')
            with j.store.connection() as db:
                rev=db.execute('SELECT revision FROM incidents').fetchone()[0]
            monitor=RecoveryMonitor(j,lambda:self.wall[0])
            op=key(); monitor.start(rev,op); monitor.start(rev,op)
            for index in range(6):
                self.wall[0]+=1
                monitor=RecoveryMonitor(j,lambda:self.wall[0])  # persisted progress/restart
                monitor.step(); monitor.step()  # same wall instant cannot double sample
                if index==4 and outcome=='relapse':
                    self.assertEqual(j.snapshot()['recovery']['status'],'verified')
            self.assertEqual(j.snapshot()['recovery']['status'],expected)
            self.assertEqual(monitor.snapshot()['status'],'completed')
            with j.store.connection() as db:
                self.assertEqual(db.execute("SELECT COUNT(*) FROM events WHERE kind='simulated_filter_replacement_completed'").fetchone()[0],1)
            monitor.fail()
            self.assertEqual(monitor.snapshot()['status'],'interrupted')


class LiveDemoDoubleTests(unittest.TestCase):
    def test_two_explicit_plans_human_reports_and_budget_no_fixture_answers(self):
        root=Path(self.enterContext(tempfile.TemporaryDirectory()))
        contexts=[]
        def send(secret,payload):
            context=json.loads(payload['messages'][1]['content']); contexts.append(context)
            # Independently expected scripted choices, labeled by test module/docstring.
            action='OBSERVE_F-17_READ_LOCAL_DP' if len(contexts)==1 else 'OBSERVE_V-08_OBSERVE_POSITION'
            value={'action_id':action,'context_revision':context['context_revision'],
                   'evidence_refs':[context['telemetry']['evidence_ref']],'explanation_code':'evidence_gap'}
            return json.dumps({'id':'chatcmpl-'+key(),'model':MODEL,'usage':{'prompt_tokens':12,'completion_tokens':8,'total_tokens':20},
                'choices':[{'finish_reason':'stop','message':{'role':'assistant','content':json.dumps(value)}}]}).encode()
        budget=Spending(root)
        app=create_demo_app(root,'http://127.0.0.1:5212',local_http=True,live=True,budget=budget,
            send=send,key_source=lambda:'TEST_ONLY_SENTINEL')
        with TestClient(app,base_url='http://127.0.0.1:5212') as client:
            headers={'Origin':'http://127.0.0.1:5212','X-FaultTrace-Demo':'1'}
            session=client.get('/api/demo/session',headers=headers).json()
            headers.update({'X-CSRF-Token':session['csrf_token'],'Idempotency-Key':key(),'X-FaultTrace-Demo-Run':''})
            response=client.post('/api/demo/start',json={},headers=headers)
            self.assertEqual(response.status_code,200)
            headers.update({'X-FaultTrace-Demo-Run':response.json()['active_run'],'X-FaultTrace-Workspace':'commander'})
            def state():
                result=client.get('/api/state',headers=headers)
                self.assertEqual(result.status_code,200)
                return result.json()
            self.assertIsNone(state()['task'])
            for asset in ('F-17','V-08'):
                s=state(); headers['Idempotency-Key']=key()
                body={'revision':s['incident']['revision']}
                one=client.post('/api/planning',json=body,headers=headers)
                two=client.post('/api/planning',json=body,headers=headers)
                self.assertEqual(one.status_code,202); self.assertEqual(one.json(),two.json())
                for _ in range(200):
                    s=state()
                    if s['planning'][-1]['status']!='pending': break
                    time.sleep(.005)
                self.assertEqual(s['task']['asset_id'],asset)
                headers['X-FaultTrace-Workspace']='operator'; headers['Idempotency-Key']=key()
                value={'revision':s['incident']['revision'],'task_revision':s['task']['revision'],'photo_id':None,
                    'decision':'independent','observed_asset_id':asset,'measurement_type':'position' if asset=='V-08' else 'differential_pressure',
                    'reading':None if asset=='V-08' else 180,'unit':None if asset=='V-08' else 'kPa',
                    'position':'intermediate' if asset=='V-08' else None,'independent':True}
                self.assertEqual(client.post('/api/tasks/'+s['task']['id']+'/observations',json=value,headers=headers).status_code,200)
                headers['X-FaultTrace-Workspace']='commander'
            s=state()
            self.assertTrue(s['journey']['assessment']['eligible'])
            self.assertEqual(s['demo']['spending']['requests_reserved'],2)
            self.assertEqual(len(contexts),2)
            serialized=json.dumps(contexts)
            for forbidden in ('private_outcome','corrected_tick','expected_reading','TEST_ONLY_SENTINEL'):
                self.assertNotIn(forbidden,serialized)
            self.assertTrue(any(o['asset_id']=='F-17' for o in contexts[1]['observations']))
            previous_run=response.json()['active_run']
            headers['Idempotency-Key']=key()
            fallback=client.post('/api/demo/restart-offline',json={},headers=headers)
            self.assertEqual(fallback.status_code,200)
            self.assertFalse(fallback.json()['inference_enabled'])
            headers['X-FaultTrace-Demo-Run']=fallback.json()['active_run']
            offline=state()
            self.assertFalse(offline['inference_enabled'])
            self.assertIn('not NVIDIA-generated',offline['task']['creation_source'])
            self.assertEqual(offline['planning'],[])
            self.assertEqual(offline['demo']['spending']['requests_reserved'],2)
            self.assertTrue((root/'runs'/previous_run/'usage.json').is_file())
            self.assertEqual(len(contexts),2)
