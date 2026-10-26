"""Private SQLite records and an OS-released single-instance process lock."""
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import uuid

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA = ROOT / ".local" / "workflow"


class WorkflowError(Exception):
    def __init__(self, code, status=400):
        self.code, self.status = code, status


def identifier(value):
    try:
        if not isinstance(value, str) or str(uuid.UUID(value)) != value:
            raise ValueError()
    except (ValueError, TypeError, AttributeError):
        raise WorkflowError("invalid_identifier", 400) from None
    return value


def now():
    return datetime.now(timezone.utc).isoformat()


class InstanceLock:
    def __init__(self, path):
        self.stream = None
        try:
            self.stream = path.open("a+b")
            self.stream.seek(0)
            if not self.stream.read(1):
                self.stream.write(b"0")
                self.stream.flush()
            self.stream.seek(0)
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(self.stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            if self.stream:
                self.stream.close()
            raise WorkflowError("workflow_instance_already_running", 503) from None

    def close(self):
        self.stream.close()  # Kernel releases the lock, including after process death.


class Store:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.images = self.directory / "images"
        self.images.mkdir(exist_ok=True)
        self.database = self.directory / "workflow.sqlite3"
        with self.connection() as db:
            db.executescript('''
              PRAGMA journal_mode=WAL;
              CREATE TABLE IF NOT EXISTS incidents (
                id TEXT PRIMARY KEY, singleton INTEGER UNIQUE CHECK(singleton=1), created_at TEXT);
              CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY, incident_id TEXT, revision INTEGER, status TEXT, created_at TEXT);
              CREATE TABLE IF NOT EXISTS evidence (
                id TEXT PRIMARY KEY, task_id TEXT, kind TEXT, origin TEXT, fixture_id TEXT,
                sha256 TEXT, width INTEGER, height INTEGER, report TEXT, created_at TEXT,
                status TEXT, submitted_revision INTEGER);
              CREATE TABLE IF NOT EXISTS analyses (
                id TEXT PRIMARY KEY, evidence_id TEXT UNIQUE, status TEXT, created_at TEXT,
                receipt TEXT, interpretation TEXT, error TEXT, accounting TEXT);
              CREATE TABLE IF NOT EXISTS operations (
                key TEXT PRIMARY KEY, fingerprint TEXT, result_id TEXT);
              CREATE TABLE IF NOT EXISTS events (
                sequence INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT, evidence_id TEXT, created_at TEXT);
            ''')
            from .photo_analysis import initialize as initialize_photos
            initialize_photos(db)
            from .simulation import initialize
            initialize(db)
            # Additive migration preserves existing FT-006 evidence and task provenance.
            for table, column, definition in (
                ('incidents', 'revision', 'INTEGER NOT NULL DEFAULT 1'),
                ('tasks', 'asset_id', "TEXT NOT NULL DEFAULT 'F-17'"),
                ('tasks', 'capability', "TEXT NOT NULL DEFAULT 'READ_LOCAL_DP'"),
                ('tasks', 'creation_source', "TEXT NOT NULL DEFAULT 'fixed simulation workflow'"),
                ('tasks', 'explanation', "TEXT NOT NULL DEFAULT 'Legacy fixed simulation observation.'"),
            ):
                if column not in {r['name'] for r in db.execute(f'PRAGMA table_info({table})')}:
                    db.execute(f'ALTER TABLE {table} ADD COLUMN {column} {definition}')
            db.executescript('''
              CREATE TABLE IF NOT EXISTS planning (
                id TEXT PRIMARY KEY, incident_id TEXT, context_revision INTEGER,
                status TEXT, created_at TEXT, context TEXT, proposal TEXT,
                receipt TEXT, error TEXT, accounting TEXT, task_id TEXT, explanation TEXT,
                UNIQUE(incident_id, context_revision));
              CREATE TRIGGER IF NOT EXISTS task_context_insert AFTER INSERT ON tasks BEGIN
                UPDATE incidents SET revision=revision+1 WHERE id=NEW.incident_id; END;
              CREATE TRIGGER IF NOT EXISTS task_context_update AFTER UPDATE ON tasks BEGIN
                UPDATE incidents SET revision=revision+1 WHERE id=NEW.incident_id; END;
            ''')

    @contextmanager
    def connection(self, write=False):
        db = sqlite3.connect(self.database, timeout=5, isolation_level=None)
        db.row_factory = sqlite3.Row
        try:
            db.execute("PRAGMA foreign_keys=ON")
            if write:
                db.execute("BEGIN IMMEDIATE")
            yield db
            if write:
                db.commit()
        except Exception:
            if write:
                db.rollback()
            raise
        finally:
            db.close()

    @staticmethod
    def operation(db, key, operation, payload):
        identifier(key)
        fingerprint = hashlib.sha256(json.dumps([operation, payload], sort_keys=True).encode()).hexdigest()
        existing = db.execute("SELECT * FROM operations WHERE key=?", (key,)).fetchone()
        if existing and existing["fingerprint"] != fingerprint:
            raise WorkflowError("idempotency_conflict", 409)
        return fingerprint, existing["result_id"] if existing else None

    @staticmethod
    def remember(db, key, fingerprint, result_id):
        db.execute("INSERT INTO operations VALUES(?,?,?)", (key, fingerprint, result_id))

    @staticmethod
    def event(db, kind, evidence_id=None):
        db.execute("INSERT INTO events(kind,evidence_id,created_at) VALUES(?,?,?)", (kind, evidence_id, now()))

    def task(self, db, task_id, revision):
        row = db.execute("SELECT * FROM tasks WHERE id=?", (identifier(task_id),)).fetchone()
        if not row:
            raise WorkflowError("task_not_found", 404)
        if type(revision) is not int or revision != row["revision"]:
            raise WorkflowError("stale_task", 409)
        return row

    def snapshot(self):
        from .planner_contract import TEMPLATES
        with self.connection() as db:
            incident = db.execute("SELECT id,created_at,revision FROM incidents").fetchone()
            tasks = [dict(r) for r in db.execute("SELECT * FROM tasks ORDER BY rowid")]
            for item in tasks:
                item['instruction'] = TEMPLATES[(item['asset_id'], item['capability'])]
            task = tasks[-1] if tasks else None
            evidence = [dict(r) for r in db.execute("SELECT * FROM evidence ORDER BY rowid")]
            for item in evidence:
                item['asset_id'] = next(t['asset_id'] for t in tasks if t['id'] == item['task_id'])
                analysis = db.execute("SELECT * FROM analyses WHERE evidence_id=?", (item["id"],)).fetchone()
                item["analysis"] = dict(analysis) if analysis else None
                if analysis:
                    photo = db.execute('SELECT contract FROM photo_analyses WHERE analysis_id=?', (analysis['id'],)).fetchone()
                    if photo:
                        item['analysis']['contract'] = photo['contract']
                    for key in ("receipt", "interpretation"):
                        item["analysis"][key] = json.loads(analysis[key]) if analysis[key] else None
                item["image_url"] = f'/api/evidence/{item["id"]}/image' if item["kind"] == "image" else None
            events = [dict(r) for r in db.execute("SELECT * FROM events ORDER BY sequence")]
            planning = [dict(r) for r in db.execute("SELECT * FROM planning ORDER BY rowid")]
            for attempt in planning:
                attempt.pop('context')  # Internal bounded input; never expose a raw provider response.
                for field in ('proposal', 'receipt'):
                    attempt[field] = json.loads(attempt[field]) if attempt[field] else None
            from .photo_planning import assessments
            photos = {p['evidence_id']: p for p in assessments(db)}
            for item in evidence:
                if item['id'] in photos:
                    item['photo_assessment'] = photos[item['id']]
            for task in tasks:
                accepted = next((p for p in planning if p['task_id'] == task['id'] and p['status'] == 'accepted'), None)
                refs = (accepted['proposal'] or {}).get('evidence_refs', []) if accepted else []
                task['source_photo_ids'] = [pid for pid in photos if 'evidence-' + pid in refs]
        return {"incident": dict(incident) if incident else None,
                "task": task, "tasks": tasks, "planning": planning,
                "planning_remaining": max(0, 4-len(planning)),
                "evidence": evidence, "events": events}
