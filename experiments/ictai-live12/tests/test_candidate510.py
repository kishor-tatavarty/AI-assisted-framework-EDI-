import unittest,json
from pathlib import Path
from collections import Counter
from ictai.evaluation59 import validate_dataset
ROOT=Path(__file__).resolve().parents[1]/'phase510'
class Candidate510Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.inputs=json.loads((ROOT/'candidate_inputs.json').read_text(encoding='utf-8'))
  cls.gold=json.loads((ROOT/'provisional_gold_NOT_FOR_CONFIRMATORY_USE.json').read_text(encoding='utf-8'))
  cls.history=json.loads((ROOT/'historical_candidate.json').read_text(encoding='utf-8'))
 def test_120_cases(self):self.assertEqual(len(self.inputs),120)
 def test_20_per_intended_category(self):
  design=json.loads((ROOT/'case_design_manifest.json').read_text(encoding='utf-8'))
  self.assertEqual(set(Counter(x['intended_category'] for x in design).values()),{20})
 def test_five_variants(self):
  self.assertEqual(set(Counter(x['type'] for x in self.inputs).values()),{24})
 def test_integrity(self):
  result=validate_dataset(self.inputs,self.gold,self.history)
  self.assertFalse(result['duplicate_history_descriptions'])
 def test_no_labels_in_inputs(self):
  self.assertTrue(all(not set(c)&{'gold','label','category','root_cause'} for c in self.inputs))
 def test_no_duplicate_case_ids(self):
  self.assertEqual(len(set(c['id'] for c in self.inputs)),120)
