
import unittest
from ictai.evaluation59 import validate_dataset,run_paired,summary
class Evaluation59Tests(unittest.TestCase):
 def setUp(self):
  self.c=[{"id":"a","symptoms":"Task failed after source delivery hold","tools":{
   "inspect_manifest":{"expected":True},"check_object_inventory":{"present":False,"count":0}}}]
  self.g={"a":"MISSING_FILE"}
  self.h=[{"id":"history-1","description":"Old partner export delay","verified":True,"stale":False,"layer":"source"}]
 def test_valid_manifest(self):
  self.assertEqual(validate_dataset(self.c,self.g,self.h)["cases"],1)
 def test_gold_leak(self):
  with self.assertRaises(ValueError):validate_dataset([{**self.c[0],"gold":"MISSING_FILE"}],self.g,self.h)
 def test_duplicate_ids(self):
  with self.assertRaises(ValueError):validate_dataset(self.c*2,self.g,self.h)
 def test_history_id_leak(self):
  with self.assertRaises(ValueError):validate_dataset(self.c,self.g,[{**self.h[0],"id":"a"}])
 def test_history_text_leak_detected(self):
  h=[{**self.h[0],"description":self.c[0]["symptoms"]}]
  self.assertEqual(validate_dataset(self.c,self.g,h)["duplicate_history_descriptions"],["a"])
 def test_bad_gold(self):
  with self.assertRaises(ValueError):validate_dataset(self.c,{"a":"BAD"},self.h)
 def test_paired_deterministic(self):
  rows=run_paired(self.c,self.g,self.h,budget=2)
  self.assertEqual(len(rows),2)
  self.assertEqual({x["arm"] for x in rows},{"B1_fixed","B2_dynamic"})
 def test_invalid_budget(self):
  with self.assertRaises(ValueError):run_paired(self.c,self.g,self.h,budget=0)
 def test_summary(self):
  rows=run_paired(self.c,self.g,self.h,budget=2)
  self.assertEqual(len(summary(rows)),2)
