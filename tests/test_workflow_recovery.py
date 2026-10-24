"""Accounting outbox and interruption tests; all provider transport is fake."""
import json
from io import BytesIO
from unittest.mock import patch

from fastapi.testclient import TestClient
from PIL import Image, PngImagePlugin

from faulttrace.ledger import load
from faulttrace.workflow.storage import InstanceLock, WorkflowError
from faulttrace.workflow.uploads import validate_upload
from test_workflow_api import WorkflowCase


class RecoveryTests(WorkflowCase):
    def test_normalization_strips_metadata_and_flattens_alpha_without_revealing_hidden_pixels(self):
        image = Image.new("RGBA", (32, 32), (10, 20, 30, 0))
        metadata = PngImagePlugin.PngInfo()
        metadata.add_text("Comment", "private metadata must not survive")
        encoded = BytesIO()
        image.save(encoded, format="PNG", pnginfo=metadata)
        result = validate_upload(encoded.getvalue(), "image/png")
        with Image.open(BytesIO(result["bytes"])) as normalized:
            self.assertEqual(normalized.mode, "RGB")
            self.assertEqual(normalized.getpixel((0, 0)), (255, 255, 255))
            self.assertEqual(normalized.info, {})

    def test_ledger_failure_retains_receipt_without_inference_replay(self):
        app = self.application()
        with TestClient(app) as client:
            task = self.start(client)
            eid = self.upload(client, task).json()["evidence_id"]
            with patch("faulttrace.ledger.os.replace", side_effect=OSError("SENTINEL_PRIVATE_KEY")):
                self.analyze(client, eid, 2)
                app.state.engine.wait()
            state = client.get("/api/state").json()
            analysis = state["evidence"][0]["analysis"]
            self.assertEqual(analysis["error"], "accounting_persistence_failed")
            self.assertEqual(analysis["accounting"], "failed")
            self.assertEqual(analysis["receipt"]["token_usage"]["total_tokens"], 30)
            self.assertNotIn("SENTINEL_PRIVATE_KEY", json.dumps(state))
            self.analyze(client, eid, 2)
            self.assertEqual(len(self.calls), 1)

    def test_receipt_outbox_recovery_is_idempotent_and_never_infers(self):
        app = self.application()
        with TestClient(app) as client:
            task = self.start(client)
            eid = self.upload(client, task).json()["evidence_id"]
            self.analyze(client, eid, 2)
            app.state.engine.wait()
            prior = client.get("/api/state").json()["evidence"][0]["analysis"]
            # Simulate death after receipt+ledger persistence but before final status commit.
            with app.state.workflow.store.connection(write=True) as db:
                db.execute("UPDATE analyses SET status='pending' WHERE id=?", (prior["id"],))
        for _ in range(2):
            with TestClient(self.application()) as client:
                result = client.get("/api/state").json()["evidence"][0]["analysis"]
                self.assertEqual(result["status"], "uncertain")
                self.assertEqual(result["receipt"], prior["receipt"])
                self.assertEqual(result["interpretation"], prior["interpretation"])
                self.assertEqual(len(load(self.ledger)), 1)
                self.assertEqual(len(self.calls), 1)

    def test_only_one_process_may_own_workflow_directory(self):
        self.data.mkdir()
        lock = InstanceLock(self.data / "instance.lock")
        try:
            with self.assertRaises(WorkflowError) as failure:
                InstanceLock(self.data / "instance.lock")
            self.assertEqual(failure.exception.code, "workflow_instance_already_running")
        finally:
            lock.close()
        again = InstanceLock(self.data / "instance.lock")
        again.close()
