import unittest
from ictai.controller import Investigation
from ictai.confirmation import confirm
from ictai.experiment52 import investigate_confirmed

class ConfirmationTests(unittest.TestCase):
    def test_missing_confirmed(self):
        ctx, result = investigate_confirmed('a','missing_file', {
            'inspect_manifest':lambda:{'expected':True},
            'check_object_inventory':lambda:{'present':False,'count':0}})
        self.assertEqual(result.status,'CONFIRMED')
        self.assertEqual(result.category,'MISSING_FILE')
    def test_schema_confirmed(self):
        ctx, result = investigate_confirmed('b','schema_drift', {
            'inspect_schema_contract':lambda:{'columns':['id']},
            'inspect_observed_schema':lambda:{'columns':['id','extra']}})
        self.assertEqual(result.status,'CONFIRMED')
        self.assertEqual(result.category,'SCHEMA_DRIFT')
    def test_conflicting_candidates_escalate(self):
        ctx, result = investigate_confirmed('c','missing_file', {
            'inspect_manifest':lambda:{'expected':True},
            'check_object_inventory':lambda:{'present':False},
            'inspect_schema_contract':lambda:{'columns':['id']},
            'inspect_observed_schema':lambda:{'columns':['different']}})
        self.assertEqual(result.status,'REVIEW_REQUIRED')
    def test_unavailable_confirmation_budget(self):
        ctx, result = investigate_confirmed('d','missing_file', {
            'inspect_manifest':lambda:{'expected':True},
            'check_object_inventory':lambda:{'present':False},
            'inspect_schema_contract':lambda:{'columns':['id']}},max_calls=2)
        self.assertEqual(result.status,'REVIEW_REQUIRED')
    def test_cold_start_abstains(self):
        ctx, result = investigate_confirmed('e','missing_file', {})
        self.assertEqual(result.status,'ABSTAINED')
    def test_bad_budget(self):
        with self.assertRaises(ValueError): investigate_confirmed('x','missing_file',{},max_calls=0)
    def test_missing_corroboration_abstains(self):
        ctx, result = investigate_confirmed('f','missing_file',{'inspect_manifest':lambda:{'expected':True}})
        self.assertEqual(result.status,'ABSTAINED')
    def test_no_ground_truth_access(self):
        ctx = Investigation('schema_drift')
        self.assertEqual(confirm(ctx).status,'INVESTIGATING')
