"""Real concurrent ASGI uploads are bounded before decoding; no provider transport."""
import asyncio
from http.cookies import SimpleCookie
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
import uuid

import httpx
from faulttrace.workflow.demo_app import create_demo_app
from faulttrace.workflow.uploads import validate_upload


class UploadCapacityTests(unittest.IsolatedAsyncioTestCase):
    async def test_third_visitor_upload_is_rejected_before_decode(self):
        with tempfile.TemporaryDirectory() as root:
            origin='http://127.0.0.1:5211'
            app=create_demo_app(root,origin,local_http=True)
            async with app.router.lifespan_context(app), httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),base_url=origin) as client:
                visitors=[]
                for _ in range(3):
                    client.cookies.clear()
                    h={'Origin':origin,'X-FaultTrace-Demo':'1','X-FaultTrace-Workspace':'operator'}
                    response=await client.get('/api/demo/session',headers=h)
                    meta=response.json(); cookie=SimpleCookie(response.headers['set-cookie'])
                    h.update({'Cookie':cookie.output(header='',sep='').strip().split(';')[0],
                        'X-CSRF-Token':meta['csrf_token'],'X-FaultTrace-Demo-Run':'','Idempotency-Key':str(uuid.uuid4())})
                    response=await client.post('/api/demo/start',json={},headers=h)
                    h['X-FaultTrace-Demo-Run']=response.json()['active_run']
                    state=(await client.get('/api/state',headers=h)).json()
                    h.update({'X-Task-Revision':str(state['task']['revision']),
                        'X-Evidence-Purpose':'reference-photo','Content-Type':'image/png','Idempotency-Key':str(uuid.uuid4())})
                    visitors.append((state['task']['id'],h))
                release=threading.Event(); entered=[]
                def decode(*args):
                    entered.append(1)
                    if not release.wait(5):
                        raise RuntimeError('test_decode_not_released')
                    return validate_upload(*args)
                data=(Path(__file__).resolve().parents[1]/'fixtures/image-evidence/panel-a.png').read_bytes()
                async def upload(visitor):
                    task,h=visitor
                    return await client.post('/api/tasks/'+task+'/images',content=data,headers=h)
                with patch('faulttrace.workflow.api.validate_upload',side_effect=decode):
                    first=[asyncio.create_task(upload(v)) for v in visitors[:2]]
                    try:
                        for _ in range(200):
                            if len(entered)==2: break
                            await asyncio.sleep(.005)
                        self.assertEqual(len(entered),2)
                        denied=await upload(visitors[2])
                        self.assertEqual(denied.status_code,429)
                        self.assertEqual(denied.json(),{'error':'demo_upload_capacity'})
                        self.assertEqual(len(entered),2)
                    finally:
                        release.set()
                        responses=await asyncio.gather(*first)
                    self.assertEqual([r.status_code for r in responses],[200,200])
