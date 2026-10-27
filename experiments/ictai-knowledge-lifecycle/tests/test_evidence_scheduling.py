
import unittest
from run_evidence_scheduling import replay,tool_order

class SchedulingTests(unittest.TestCase):
    def test_schema_candidate_before_strict(self):
        case={'tools':{'inspect_schema_contract':{'columns':['a']},'inspect_observed_schema':{'columns':['b']},'inspect_task_execution':{'failed':False,'run_id':'r'},'read_run_events':{'execution_error':False,'run_id':'r'}}}
        row=replay(case,list(case['tools']))
        self.assertEqual(row['first_supported_candidate_call'],2)
        self.assertEqual(row['first_strict_confirmation_call'],4)
        self.assertEqual(row['final_category'],'SCHEMA_DRIFT')

    def test_competing_cause_requires_review(self):
        case={'tools':{'inspect_schema_contract':{'columns':['a']},'inspect_observed_schema':{'columns':['b']},'inspect_task_execution':{'failed':True,'run_id':'r'},'read_run_events':{'execution_error':True,'run_id':'r'}}}
        row=replay(case,list(case['tools']))
        self.assertEqual(row['final_status'],'REVIEW_REQUIRED')
        self.assertIsNone(row['first_strict_confirmation_call'])

    def test_order_preserves_all_tools(self):
        case={'tools':{'inspect_manifest':{},'inspect_task_execution':{},'read_run_events':{}}}
        self.assertEqual(set(tool_order(case,['pipeline'])),set(case['tools']))
