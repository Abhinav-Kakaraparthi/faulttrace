"""Offline ASGI tests. Fake transport only; temporary private data and ledger."""
from io import BytesIO
import json
from pathlib import Path
import re
import tempfile
import threading
import unittest
import uuid

from fastapi.testclient import TestClient
from PIL import Image

from faulttrace.accounting import VISION_MODEL
from faulttrace.ledger import load, summarize
from faulttrace.workflow.api import create_app
from faulttrace.workflow.storage import Store
from faulttrace.workflow.uploads import MAX_UPLOAD

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures/image-evidence"
LOCAL = {"X-FaultTrace-Local": "1"}


def key():
    return str(uuid.uuid4())


class WorkflowCase(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.data = Path(self.directory.name) / "data"
        self.ledger = Path(self.directory.name) / "usage.json"
        self.calls = []
        self.readability = "readable"
        self.invalid = False

    def send(self, secret, payload):
        self.calls.append(payload)
        # A separate writer can acquire SQLite while the fake network call runs.
        with Store(self.data).connection(write=True):
            pass
        ref = re.search(r'evidence_ref \("([^"]+)"\)', payload["messages"][0]["content"][0]["text"])[1]
        result = {"readability": self.readability, "reading": 180 if self.readability == "readable" else None,
                  "unit": "kPa" if self.readability == "readable" else None, "evidence_ref": "invented" if self.invalid else ref}
        return json.dumps({"id": "chatcmpl-aabb-1234", "model": VISION_MODEL,
                           "choices": [{"finish_reason": "stop", "message": {"role": "assistant", "content": json.dumps(result)}}],
                           "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}}).encode()

    def application(self, **kwargs):
        return create_app(self.data, self.ledger, kwargs.pop("send", self.send),
                          kwargs.pop("enabled", True), kwargs.pop("key_source", lambda: "SENTINEL_PRIVATE_KEY"), **kwargs)

    def post(self, client, path, body, request_key=None):
        return client.post(path, json=body, headers={**LOCAL, "Idempotency-Key": request_key or key()})

    def start(self, client):
        self.assertEqual(self.post(client, "/api/incidents", {}).status_code, 200)
        return client.get("/api/state").json()["task"]

    def upload(self, client, task, data=None, request_key=None, fixture="panel-a", mime="image/png"):
        headers = {**LOCAL, "Idempotency-Key": request_key or key(), "X-Task-Revision": str(task["revision"]), "Content-Type": mime}
        if fixture:
            headers["X-Fixture-Id"] = fixture
        return client.post(f'/api/tasks/{task["id"]}/images', content=(FIXTURES / "panel-a.png").read_bytes() if data is None else data, headers=headers)

    def analyze(self, client, evidence_id, revision, request_key=None):
        return self.post(client, f"/api/evidence/{evidence_id}/analyze", {"revision": revision}, request_key)

class WorkflowTests(WorkflowCase):
    def test_two_clients_persistence_and_analysis_once(self):
        app = self.application()
        with TestClient(app) as commander:
            operator = TestClient(app)
            task = self.start(commander)
            self.assertEqual(operator.get("/api/state").json()["task"], task)
            upload_key = key()
            uploaded = self.upload(operator, task, request_key=upload_key)
            self.assertEqual(uploaded.status_code, 200)
            eid = uploaded.json()["evidence_id"]
            self.assertEqual(self.upload(operator, task, request_key=upload_key).json()["evidence_id"], eid)
            state = commander.get("/api/state").json()
            self.assertEqual(state["evidence"][0]["origin"], "synthetic-fixture")
            self.assertEqual(len(self.calls), 0)
            revision = state["task"]["revision"]
            analysis_key = key()
            first = self.analyze(operator, eid, revision, analysis_key)
            self.assertEqual(first.status_code, 202)
            app.state.engine.wait()
            self.assertEqual(self.analyze(operator, eid, revision, analysis_key).json(), first.json())
            self.assertEqual(self.analyze(operator, eid, revision).json(), first.json())
            self.assertEqual(len(self.calls), 1)
            state = commander.get("/api/state").json()
            result = state["evidence"][0]
            self.assertEqual(result["status"], "accepted")
            self.assertEqual(result["analysis"]["interpretation"]["reading"], 180)
            self.assertEqual(result["analysis"]["receipt"]["token_usage"]["total_tokens"], 30)
            self.assertEqual(len(load(self.ledger)), 1)
            self.assertEqual(operator.get(result["image_url"]).status_code, 200)
        with TestClient(self.application()) as restarted:
            self.assertEqual(restarted.get("/api/state").json()["evidence"], state["evidence"])
            self.assertEqual(restarted.get("/api/state").json()["task"], state["task"])
            self.assertEqual(len(self.calls), 1)
            self.assertEqual(self.upload(restarted, task, request_key=upload_key).json()["evidence_id"], eid)
            self.assertEqual(self.analyze(restarted, eid, revision, analysis_key).json(), first.json())
            self.assertEqual(len(load(self.ledger)), 1)

    def test_stale_submissions_conflicting_keys_and_old_evidence(self):
        with TestClient(self.application()) as client:
            task = self.start(client)
            request_key = key()
            eid = self.upload(client, task, request_key=request_key).json()["evidence_id"]
            self.assertEqual(self.upload(client, task).status_code, 409)
            self.assertEqual(self.upload(client, task, data=(FIXTURES / "panel-b.png").read_bytes(),
                                         fixture="panel-b", request_key=request_key).json()["error"], "idempotency_conflict")
            current = client.get("/api/state").json()["task"]
            self.assertEqual(self.analyze(client, eid, task["revision"]).json()["error"], "stale_task")
            self.post(client, f'/api/tasks/{task["id"]}/reopen', {"revision": current["revision"]})
            self.assertEqual(client.get("/api/state").json()["evidence"][0]["status"], "stale")
            fresh = client.get("/api/state").json()["task"]
            self.assertEqual(self.analyze(client, eid, fresh["revision"]).status_code, 409)
            self.assertEqual(len(self.calls), 0)

    def test_upload_bounds_real_bytes_dimensions_and_provenance(self):
        with TestClient(self.application()) as client:
            task = self.start(client)
            for data, mime, fixture in [(b"not_png", "image/png", None),
                                        (b"x" * (MAX_UPLOAD + 1), "image/png", None),
                                        ((FIXTURES / "panel-a.png").read_bytes(), "image/jpeg", None),
                                        ((FIXTURES / "panel-a.png").read_bytes(), "image/png", "panel-b")]:
                with self.subTest(mime=mime, fixture=fixture):
                    self.assertGreaterEqual(self.upload(client, task, data=data, mime=mime, fixture=fixture).status_code, 400)
            output = BytesIO()
            Image.new("RGB", (2049, 16)).save(output, format="PNG")
            self.assertEqual(self.upload(client, task, data=output.getvalue(), fixture=None).status_code, 400)
            output = BytesIO()
            Image.new("RGB", (32, 32), "gray").save(output, format="JPEG")
            accepted = self.upload(client, task, data=output.getvalue(), mime="image/jpeg", fixture=None)
            self.assertEqual(accepted.status_code, 200)
            item = client.get("/api/state").json()["evidence"][0]
            self.assertEqual(item["origin"], "user-upload")
            self.assertEqual(client.get(item["image_url"]).headers["content-type"], "image/png")
            self.assertGreaterEqual(client.get("/api/evidence/not-a-path/image").status_code, 400)

    def test_unreadable_and_human_refusals_never_invent_values(self):
        self.readability = "unreadable"
        app = self.application()
        with TestClient(app) as client:
            task = self.start(client)
            eid = self.upload(client, task).json()["evidence_id"]
            self.analyze(client, eid, client.get("/api/state").json()["task"]["revision"])
            app.state.engine.wait()
            state = client.get("/api/state").json()
            self.assertEqual(state["evidence"][0]["status"], "unreadable")
            self.assertIsNone(state["evidence"][0]["analysis"]["interpretation"]["reading"])
            self.assertEqual(state["task"]["status"], "needs_evidence")
            for report in ("unreadable", "cannot-access", "wrong-equipment"):
                task = client.get("/api/state").json()["task"]
                response = self.post(client, f'/api/tasks/{task["id"]}/reports', {"revision": task["revision"], "report": report})
                self.assertEqual(response.status_code, 200)
                item = client.get("/api/state").json()["evidence"][-1]
                self.assertEqual(item["origin"], "human-report")
                self.assertIsNone(item["analysis"])
                self.assertIsNone(item["image_url"])
            self.assertEqual(len(self.calls), 1)

    def test_provider_failure_accounting_and_secret_non_disclosure(self):
        self.invalid = True
        app = self.application()
        with TestClient(app) as client:
            task = self.start(client)
            eid = self.upload(client, task).json()["evidence_id"]
            self.analyze(client, eid, client.get("/api/state").json()["task"]["revision"])
            app.state.engine.wait()
            state = client.get("/api/state").json()
            receipt = state["evidence"][0]["analysis"]["receipt"]
            self.assertEqual(receipt["token_usage"]["total_tokens"], 30)
            self.assertEqual(state["evidence"][0]["status"], "failed")
            self.assertEqual(summarize(load(self.ledger))["known_tokens"]["total_tokens"], 30)
            self.assertNotIn("SENTINEL_PRIVATE_KEY", json.dumps(state))
            self.assertNotIn("SENTINEL_PRIVATE_KEY", self.ledger.read_text())

    def test_network_failure_unknown_usage_no_replay_on_restart(self):
        def failure(*args):
            self.calls.append(True)
            raise RuntimeError("SENTINEL_PRIVATE_KEY private provider body")
        app = self.application(send=failure)
        with TestClient(app) as client:
            task = self.start(client)
            eid = self.upload(client, task).json()["evidence_id"]
            self.analyze(client, eid, client.get("/api/state").json()["task"]["revision"])
            app.state.engine.wait()
            state = client.get("/api/state").json()
            self.assertEqual(state["evidence"][0]["status"], "failed")
            self.assertIsNone(state["evidence"][0]["analysis"]["receipt"]["token_usage"])
            self.assertNotIn("SENTINEL_PRIVATE_KEY", json.dumps(state))
        with TestClient(self.application(send=failure)) as client:
            self.assertEqual(client.get("/api/state").json()["evidence"][0]["status"], "failed")
            self.assertEqual(len(self.calls), 1)

    def test_disabled_inference_missing_credentials_and_origin_boundary(self):
        with TestClient(self.application(enabled=False)) as client:
            task = self.start(client)
            eid = self.upload(client, task).json()["evidence_id"]
            self.assertEqual(self.analyze(client, eid, 2).json()["error"], "inference_disabled")
            self.assertEqual(client.post("/api/incidents", json={}, headers={**LOCAL, "Origin": "https://untrusted.invalid"}).status_code, 403)
            self.assertEqual(client.post("/api/incidents", json={}).status_code, 403)
            self.assertEqual(len(self.calls), 0)
        with TestClient(self.application(key_source=lambda: None)) as client:
            self.assertEqual(self.analyze(client, eid, 2).json()["error"], "missing_credentials")

    def test_interrupted_reservation_becomes_uncertain_without_provider_call(self):
        app = self.application()
        with TestClient(app) as client:
            task = self.start(client)
            eid = self.upload(client, task).json()["evidence_id"]
            reserved, created = app.state.workflow.reserve_analysis(eid, 2, key())
            self.assertTrue(created)  # Durable reservation, simulate death before starting worker.
        with TestClient(self.application()) as client:
            item = client.get("/api/state").json()["evidence"][0]
            self.assertEqual(item["status"], "uncertain")
            self.assertEqual(item["analysis"]["error"], "analysis_interrupted")
            self.assertEqual(item["analysis"]["receipt"]["attempt_id"], reserved)
            self.assertIsNone(item["analysis"]["receipt"]["transport_invoked"])
            self.assertEqual(len(load(self.ledger)), 1)
            self.assertEqual(len(self.calls), 0)

    def test_pending_visible_and_duplicate_clicks_during_call(self):
        entered, release = threading.Event(), threading.Event()
        def blocked(*args):
            entered.set()
            self.assertTrue(release.wait(5))
            return self.send(*args)
        app = self.application(send=blocked)
        with TestClient(app) as client:
            task = self.start(client)
            eid = self.upload(client, task).json()["evidence_id"]
            first = self.analyze(client, eid, 2)
            self.assertTrue(entered.wait(5))
            try:
                state = client.get("/api/state").json()
                self.assertEqual(state["task"]["status"], "analyzing")
                self.assertEqual(self.analyze(client, eid, 2).json(), first.json())
                self.assertEqual(self.post(client, f'/api/tasks/{task["id"]}/reopen', {"revision": state["task"]["revision"]}).status_code, 409)
            finally:
                release.set()
            app.state.engine.wait()
            self.assertEqual(len(self.calls), 1)


if __name__ == "__main__":
    unittest.main()
