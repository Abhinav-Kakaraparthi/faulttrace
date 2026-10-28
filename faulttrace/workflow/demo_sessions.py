"""Bounded durable cookie sessions; investigation directories are server-generated."""
from contextlib import closing, contextmanager
import hashlib
from pathlib import Path
import re
import secrets
import sqlite3
import time
import uuid

from .storage import WorkflowError, identifier


class DemoSessions:
    def __init__(self, directory, clock=time.time, ttl=7200, limit=32, run_limit=3, live=False):
        self.root, self.clock, self.ttl = Path(directory), clock, ttl
        self.limit, self.run_limit = limit, run_limit
        self.live = live
        self.root.mkdir(parents=True, exist_ok=True)
        with self.db() as db:
            db.executescript('''CREATE TABLE IF NOT EXISTS sessions(
                hash TEXT PRIMARY KEY, csrf TEXT, expires REAL, run TEXT, runs INTEGER, ended INTEGER);
                CREATE TABLE IF NOT EXISTS operations(
                session TEXT,key TEXT,operation TEXT,prior TEXT,result TEXT,PRIMARY KEY(session,key));
                CREATE TABLE IF NOT EXISTS run_modes(run TEXT PRIMARY KEY,live INTEGER);''')

    @contextmanager
    def db(self):
        with closing(sqlite3.connect(self.root / 'sessions.sqlite3', timeout=5)) as db, db:
            db.row_factory = sqlite3.Row
            yield db

    def get(self, cookie):
        if not isinstance(cookie, str) or not re.fullmatch(r'[A-Za-z0-9_-]{43}', cookie):
            raise WorkflowError('demo_session_required', 401)
        digest = hashlib.sha256(cookie.encode()).hexdigest()
        with self.db() as db:
            row = db.execute('SELECT * FROM sessions WHERE hash=?', (digest,)).fetchone()
        if not row or row['ended'] or row['expires'] <= self.clock():
            raise WorkflowError('demo_session_expired', 401)
        return dict(row)

    def new(self):
        cookie, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        digest = hashlib.sha256(cookie.encode()).hexdigest()
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            if db.execute('SELECT COUNT(*) FROM sessions').fetchone()[0] >= self.limit:
                raise WorkflowError('demo_capacity', 503)
            db.execute('INSERT INTO sessions VALUES(?,?,?,NULL,0,0)',
                       (digest, csrf, self.clock() + self.ttl))
        return cookie, self.get(cookie)

    def public(self, row):
        live = self.live
        if row['run']:
            with self.db() as db:
                mode = db.execute('SELECT live FROM run_modes WHERE run=?', (row['run'],)).fetchone()
            live = live and bool(mode and mode['live'])
        return {'active_run': row['run'], 'csrf_token': row['csrf'],
                'expires_at': row['expires'], 'inference_enabled': live,
                'privileges': 'One demo visitor may use both workspaces; not separate employee identities.'}

    def check_csrf(self, row, value):
        if not isinstance(value, str) or not secrets.compare_digest(value, row['csrf']):
            raise WorkflowError('demo_csrf_required', 403)

    def change(self, cookie, key, operation, prior):
        identifier(key)
        row = self.get(cookie)
        requested_live = self.public(row)['inference_enabled'] if row['run'] and operation == 'restart' else self.live
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            old = db.execute('SELECT * FROM operations WHERE session=? AND key=?', (row['hash'], key)).fetchone()
            if old:
                if old['operation'] != operation or old['prior'] != prior:
                    raise WorkflowError('idempotency_conflict', 409)
                if row['run'] != old['result']:
                    raise WorkflowError('demo_session_changed', 409)
                return row
            if prior != (row['run'] or ''):
                raise WorkflowError('demo_session_changed', 409)
            if operation == 'start' and row['run']:
                result = row['run']
            else:
                if row['runs'] >= self.run_limit:
                    raise WorkflowError('demo_restart_limit', 429)
                result = str(uuid.uuid4())
                db.execute('UPDATE sessions SET run=?,runs=runs+1 WHERE hash=?', (result, row['hash']))
                db.execute('INSERT INTO run_modes VALUES(?,?)', (result, int(requested_live and operation != 'restart-offline')))
            db.execute('INSERT INTO operations VALUES(?,?,?,?,?)', (row['hash'],key,operation,prior,result))
        return self.get(cookie)

    def end(self, row):
        with self.db() as db:
            db.execute('UPDATE sessions SET ended=1 WHERE hash=?', (row['hash'],))
