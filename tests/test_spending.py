"""Persistent admission policy, independent of provider billing and tokenization."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import tempfile
import unittest
import uuid

from faulttrace.workflow.spending import Spending, ALLOWANCE
from faulttrace.workflow.storage import WorkflowError


class SpendingTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory()))

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
