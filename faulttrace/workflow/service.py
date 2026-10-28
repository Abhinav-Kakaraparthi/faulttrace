"""Revision checks, durable submissions and idempotency; no equipment actions."""
import os
import threading
import uuid

from .storage import Store, WorkflowError, identifier, now


class Workflow:
    def __init__(self, store: Store):
        self.store = store
        self.write_lock = threading.RLock()

    def start(self, key):
        with self.write_lock, self.store.connection(write=True) as db:
            fingerprint, existing = self.store.operation(db, key, "start", {})
            if existing:
                return existing
            incident = db.execute("SELECT id FROM incidents").fetchone()
            incident_id = incident["id"] if incident else str(uuid.uuid4())
            if not incident:
                db.execute("INSERT INTO incidents(id,singleton,created_at) VALUES(?,1,?)", (incident_id, now()))
                self.store.event(db, "simulated_incident_started")
            self.store.remember(db, key, fingerprint, incident_id)
        return incident_id

    def submit(self, task_id, revision, key, *, image=None, report=None, reference_photo=False):
        payload = {"task": task_id, "revision": revision, "report": report,
                   "sha256": image["sha256"] if image else None,
                   "fixture_id": image["fixture_id"] if image else None}
        # Preserve legacy operation fingerprints; only the new collection mode adds a field.
        if reference_photo:
            if not image or image['fixture_id'] is not None:
                raise WorkflowError('invalid_evidence_purpose', 400)
            payload['purpose'] = 'reference-photo'
        with self.write_lock, self.store.connection(write=True) as db:
            fingerprint, existing = self.store.operation(db, key, "submit", payload)
            if existing:
                return existing
            task = self.store.task(db, task_id, revision)
            latest = db.execute('SELECT id FROM tasks ORDER BY rowid DESC LIMIT 1').fetchone()
            if latest['id'] != task_id:
                raise WorkflowError('stale_task', 409)
            if task["status"] not in ("awaiting", "needs_evidence"):
                raise WorkflowError("task_not_accepting_evidence", 409)
            if not image:
                allowed = (('cannot-access', 'wrong-equipment', 'unreadable') if task['asset_id'] == 'F-17'
                           else ('open', 'intermediate', 'closed', 'cannot determine', 'cannot-access', 'wrong-equipment'))
                if type(report) is not str or report not in allowed:
                    raise WorkflowError("invalid_report", 400)
            if image and task['asset_id'] != 'F-17' and not (reference_photo and task['asset_id'] == 'V-08'):
                raise WorkflowError('invalid_report', 400)
            evidence_id = str(uuid.uuid4())
            status = ("collected" if reference_photo else "pending" if image else "unreadable" if report == "unreadable"
                      else "accepted" if task['asset_id'] == 'V-08' and report in ('open', 'intermediate', 'closed')
                      else "refused")
            if image:
                temporary = self.store.images / (evidence_id + ".tmp")
                with temporary.open("wb") as stream:
                    stream.write(image["bytes"])
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(temporary, self.store.images / (evidence_id + ".png"))
            db.execute("UPDATE evidence SET status='stale' WHERE task_id=? AND status='pending'", (task_id,))
            db.execute("INSERT INTO evidence VALUES(?,?,?,?,?,?,?,?,?,?,?,?)", (
                evidence_id, task_id, "image" if image else "report",
                image["origin"] if image else "human-report", image["fixture_id"] if image else None,
                image["sha256"] if image else None, image["width"] if image else None,
                image["height"] if image else None, report, now(), status, revision))
            db.execute("UPDATE tasks SET revision=revision+1,status=? WHERE id=?",
                       (task["status"] if reference_photo else "submitted" if image else "observed" if status == 'accepted' else "needs_evidence", task_id))
            self.store.event(db, "reference_photo_collected" if reference_photo else "image_submitted" if image else "operator_reported_" + report, evidence_id)
            self.store.remember(db, key, fingerprint, evidence_id)
        return evidence_id

    def reopen(self, task_id, revision, key):
        with self.write_lock, self.store.connection(write=True) as db:
            fingerprint, existing = self.store.operation(db, key, "reopen", [task_id, revision])
            if existing:
                return existing
            task = self.store.task(db, task_id, revision)
            if task["status"] == "analyzing":
                raise WorkflowError("analysis_in_progress", 409)
            if db.execute('SELECT id FROM tasks ORDER BY rowid DESC LIMIT 1').fetchone()['id'] != task_id:
                raise WorkflowError('stale_task', 409)
            other = db.execute("SELECT id FROM tasks WHERE id<>? AND status IN ('awaiting','submitted','analyzing')", (task_id,)).fetchone()
            if other:
                raise WorkflowError('active_task_conflict', 409)
            db.execute("UPDATE evidence SET status='stale' WHERE task_id=? AND status IN ('pending','collected')", (task_id,))
            db.execute("UPDATE tasks SET revision=revision+1,status='awaiting' WHERE id=?", (task_id,))
            self.store.event(db, "observation_reissued")
            self.store.remember(db, key, fingerprint, task_id)
        return task_id

    def reserve_analysis(self, evidence_id, revision, key):
        with self.write_lock, self.store.connection(write=True) as db:
            fingerprint, duplicate = self.store.operation(db, key, "analyze", [evidence_id, revision])
            if duplicate:
                return duplicate, False
            evidence = db.execute("SELECT * FROM evidence WHERE id=?", (identifier(evidence_id),)).fetchone()
            if not evidence:
                raise WorkflowError("evidence_not_found", 404)
            if evidence['status'] == 'collected':
                raise WorkflowError('photo_analysis_unsupported', 409)
            existing = db.execute("SELECT id FROM analyses WHERE evidence_id=?", (evidence_id,)).fetchone()
            if existing:
                self.store.remember(db, key, fingerprint, existing["id"])
                return existing["id"], False  # Different click key still cannot repeat a call.
            task = self.store.task(db, evidence["task_id"], revision)
            if evidence['kind'] == 'image' and task['asset_id'] != 'F-17':
                raise WorkflowError('photo_analysis_unsupported', 409)
            latest = db.execute("SELECT id FROM evidence WHERE task_id=? ORDER BY rowid DESC LIMIT 1",
                                (task["id"],)).fetchone()
            if evidence["kind"] != "image" or evidence["status"] != "pending" or latest["id"] != evidence_id:
                raise WorkflowError("stale_or_unanalyzable_evidence", 409)
            analysis_id = str(uuid.uuid4())
            if getattr(self, 'budget', None):
                self.budget.reserve('fixture', analysis_id)
            db.execute("INSERT INTO analyses VALUES(?,?,'pending',?,NULL,NULL,NULL,'pending')",
                       (analysis_id, evidence_id, now()))
            db.execute("UPDATE tasks SET revision=revision+1,status='analyzing' WHERE id=?", (task["id"],))
            self.store.event(db, "analysis_explicitly_requested", evidence_id)
            self.store.remember(db, key, fingerprint, analysis_id)
        return analysis_id, True
