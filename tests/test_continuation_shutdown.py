"""Continuation teardown must finish an active SQLite tick before releasing storage."""
import asyncio
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

from faulttrace.workflow.api import create_app
from faulttrace.workflow.continuation import Continuation


class ContinuationShutdownTests(unittest.IsolatedAsyncioTestCase):
    async def test_shutdown_drains_running_tick_before_releasing_instance(self):
        started, release, finished = threading.Event(), threading.Event(), threading.Event()

        def blocking_tick(runner):
            with runner.store.connection() as db:
                db.execute('SELECT 1')
                started.set()
                if not release.wait(5):
                    raise AssertionError('test_tick_not_released')
            finished.set()

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            app = create_app(root / 'data', root / 'usage.json', enabled=False)
            with patch.object(Continuation, 'step', blocking_tick):
                lifespan = app.router.lifespan_context(app)
                await lifespan.__aenter__()
                closing = None
                try:
                    self.assertTrue(await asyncio.to_thread(started.wait, 3))
                    closing = asyncio.create_task(lifespan.__aexit__(None, None, None))
                    await asyncio.sleep(.05)
                    self.assertFalse(closing.done(), 'storage cannot close while its tick is active')
                    self.assertFalse(finished.is_set())
                finally:
                    release.set()
                    if closing is None:
                        await lifespan.__aexit__(None, None, None)
                    else:
                        await asyncio.wait_for(closing, timeout=3)
                self.assertTrue(finished.is_set())
            # Windows cleanup below also verifies no SQLite file remains held open.
