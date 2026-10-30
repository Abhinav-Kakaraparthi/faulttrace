"""Persistent admission policy, independent of provider billing and tokenization."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import tempfile
import unittest
import uuid
from unittest.mock import patch

from faulttrace.workflow.spending import Spending, ALLOWANCE
from faulttrace.workflow.storage import WorkflowError


class SpendingTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory()))

    def test_live_factory_overrides_only_global_admission_cap(self):
        from faulttrace.workflow.demo_app import create_demo
        with patch.dict('os.environ', {'FAULTTRACE_DEMO_ROOT':str(self.root),
                'FAULTTRACE_DEMO_ORIGIN':'https://test.invalid', 'FAULTTRACE_DEMO_LIVE':'1',
                'FAULTTRACE_ALLOW_INFERENCE':'1', 'NEBIUS_API_KEY':'OFFLINE_TEST_ONLY'}), \
                patch('faulttrace.workflow.spending.Spending', wraps=Spending) as factory, \
                patch('faulttrace.workflow.demo_app.create_demo_app') as build:
            create_demo()
        factory.assert_called_once_with(str(self.root), tokens=1265664)
        budget = build.call_args.kwargs['budget']
        self.assertEqual((budget.requests, budget.tokens, budget.session_requests,
                          budget.session_tokens, budget.concurrent), (12,1265664,6,600000,2))

    def test_narrow_cap_extension_keeps_history_and_admits_exactly_one_photo(self):
        original = Spending(self.root)
        for index in range(10):
            visitor = 'current' if index == 0 else 'other-' + str(index)
            operation = 'planning' if index < 7 else ('photo' if index < 9 else 'documentation')
            aid = str(uuid.uuid4())
            original.reserve(visitor, operation, aid)
            if index != 1:
                original.settle(visitor, aid, {'usage_status':'missing'})
        original.recover_pending()
        with original.db() as db:
            before = [tuple(r) for r in db.execute('SELECT * FROM reservations ORDER BY id')]
        self.assertEqual(sum(r[4] for r in before), 1001472)
        aid = str(uuid.uuid4())
        with self.assertRaises(WorkflowError) as error:
            original.reserve('current', 'photo', aid)
        self.assertEqual(error.exception.code, 'spending_budget_exhausted')
        extended = Spending(self.root, tokens=1265664)
        extended.reserve('current', 'photo', aid)
        extended.reserve('current', 'photo', aid)  # Replay consumes no additional slot.
        with extended.db() as db:
            after = [tuple(r) for r in db.execute('SELECT * FROM reservations WHERE id!=? ORDER BY id', (aid,))]
            count, charged = db.execute('SELECT COUNT(*),SUM(charged) FROM reservations').fetchone()
        self.assertEqual(after, before)
        self.assertEqual((count, charged), (11,1265664))
        self.assertEqual(extended.summary('current')['token_allowance_consumed'], 331776)
        with self.assertRaises(WorkflowError) as error:
            extended.reserve('another', 'planning', str(uuid.uuid4()))
        self.assertEqual(error.exception.code, 'spending_budget_exhausted')

    def test_concurrent_admission_is_global_across_visitors(self):
        budget = Spending(self.root)
        def attempt(n):
            try:
                budget.for_session(str(n)).reserve('planning', str(uuid.uuid4()))
                return 'admitted'
            except WorkflowError as error:
                return error.code
        with ThreadPoolExecutor(max_workers=12) as workers:
            outcomes = list(workers.map(attempt, range(12)))
        self.assertEqual(outcomes.count('admitted'), 2)
        self.assertEqual(outcomes.count('spending_concurrency_limit'), 10)

    def test_missing_partial_invalid_counts_and_restart_never_refund(self):
        budget = Spending(self.root, concurrent=6)
        own = budget.for_session('visitor')
        for usage in (None, {'prompt_tokens': 4}, {'prompt_tokens': True}, {'total_tokens': 20}):
            aid = str(uuid.uuid4())
            own.reserve('planning', aid)
            own.reserve('planning', aid)
            receipt = {'token_usage': usage, 'usage_status': 'missing' if usage is None else 'partial'}
            own.settle(aid, receipt)
            own.settle(aid, receipt)
        aid = str(uuid.uuid4())
        own.reserve('planning', aid)
        restarted = Spending(self.root)
        restarted.recover_pending()
        summary = restarted.summary('visitor')
        self.assertEqual(summary['requests_reserved'], 5)
        self.assertEqual(summary['token_allowance_consumed'], 5*ALLOWANCE['planning'])
        self.assertEqual(summary['uncertain_or_pending'], 1)

    def test_request_token_session_caps_and_conflicting_duplicates(self):
        budget = Spending(self.root, requests=2, session_requests=1)
        aid = str(uuid.uuid4())
        budget.reserve('one', 'planning', aid)
        with self.assertRaisesRegex(WorkflowError, '') as error:
            budget.reserve('two', 'planning', aid)
        self.assertEqual(error.exception.code, 'idempotency_conflict')
        budget.settle('one', aid, {'usage_status':'valid', 'token_usage':{'total_tokens':1}})
        with self.assertRaises(WorkflowError) as error:
            budget.reserve('one', 'planning', str(uuid.uuid4()))
        self.assertEqual(error.exception.code, 'spending_budget_exhausted')
        budget.reserve('two', 'documentation', str(uuid.uuid4()))
        with self.assertRaises(WorkflowError):
            budget.reserve('three', 'documentation', str(uuid.uuid4()))
        other = Spending(self.root/'small', tokens=ALLOWANCE['planning']-1)
        with self.assertRaises(WorkflowError):
            other.reserve('one','planning',str(uuid.uuid4()))

    def test_overrun_is_preserved_and_accounting_conflict_rejected(self):
        budget = Spending(self.root)
        aid = str(uuid.uuid4())
        budget.reserve('one', 'planning', aid)
        receipt = {'usage_status':'valid','token_usage':{'total_tokens':2000000}}
        budget.settle('one', aid, receipt)
        self.assertEqual(budget.summary('one')['token_allowance_consumed'], 2000000)
        with self.assertRaises(WorkflowError):
            budget.settle('one', aid, {'usage_status':'missing'})
        with self.assertRaises(WorkflowError):
            budget.reserve('other', 'planning', str(uuid.uuid4()))

    def test_container_revision_fallback_is_strict_and_does_not_hide_dirty_git(self):
        from faulttrace.workflow.analysis import source_revision
        with patch('faulttrace.workflow.analysis.subprocess.check_output', side_effect=FileNotFoundError()), patch.dict('os.environ', {'FAULTTRACE_BUILD_REVISION':'a'*40}):
            self.assertEqual(source_revision(),'a'*40)
        with patch('faulttrace.workflow.analysis.subprocess.check_output', side_effect=FileNotFoundError()), patch.dict('os.environ', {'FAULTTRACE_BUILD_REVISION':'PRIVATE_SENTINEL'}):
            self.assertIsNone(source_revision())
        with patch('faulttrace.workflow.analysis.subprocess.check_output', return_value=b'dirty'), patch.dict('os.environ', {'FAULTTRACE_BUILD_REVISION':'a'*40}):
            self.assertIsNone(source_revision())
