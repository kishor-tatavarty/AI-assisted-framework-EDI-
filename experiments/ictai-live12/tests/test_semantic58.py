
import unittest,tempfile
from ictai.semantic_fixtures58 import build
from ictai.semantic58 import run,retrieve,evaluate,summarize,ARMS
class Semantic58Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.temp=tempfile.TemporaryDirectory();cls.cases,cls.gold,cls.history=build(cls.temp.name)
 @classmethod
 def tearDownClass(cls):cls.temp.cleanup()
 def test_fixture_count(self):
  self.assertEqual(len(self.cases),24)
  self.assertEqual(len(self.history),12)
  self.assertEqual(len(set(self.gold.values())-{"INSUFFICIENT_EVIDENCE"}),6)
 def test_no_gold_in_input(self):
  self.assertTrue(all("gold" not in c for c in self.cases))
 def test_reject_gold_leakage(self):
  with self.assertRaises(ValueError):run({**self.cases[0],"gold":"MISSING_FILE"},"B1_fixed")
 def test_disjoint_ids(self):
  self.assertFalse(set(c["id"] for c in self.cases)&set(h["id"] for h in self.history))
 def test_stale_unverified_filtered(self):
  x=retrieve([{"id":"a","description":"vendor delivery","layer":"source","verified":False},
              {"id":"b","description":"vendor delivery","layer":"source","verified":True,"stale":True}], "vendor delivery")
  self.assertEqual(x,[])
 def test_fixed_and_dynamic_run(self):
  for arm in ARMS[:2]:
   result=run(self.cases[0],arm)
   self.assertIn(result["status"],("CONFIRMED","ABSTAINED","REVIEW_REQUIRED"))
   self.assertLessEqual(result["tool_calls"],12)
 def test_all_six_can_confirm(self):
  for i in range(0,24,4):
   case=self.cases[i]
   result=run(case,"B1_fixed")
   self.assertEqual(result["prediction"],self.gold[case["id"]])
   self.assertEqual(result["status"],"CONFIRMED")
 def test_incomplete_abstains(self):
  for i in range(3,24,4):
   case=self.cases[i];result=run(case,"B1_fixed")
   self.assertNotEqual(result["status"],"CONFIRMED")
 def test_llm_routes_with_mock(self):
  def mock(messages):
   import json
   payload=json.loads(messages[-1]["content"])
   return {"next_layer":payload["available_layers"][0],"hypotheses":[],"open_questions":[],"evidence_refs":[]}
  result=run(self.cases[0],"B3_llm",model=mock)
  self.assertGreater(result["llm_attempts"],0)
 def test_knowledge_hits_logged(self):
  def mock(messages):
   import json
   payload=json.loads(messages[-1]["content"])
   return {"next_layer":payload["available_layers"][0],"hypotheses":[],"open_questions":[],"evidence_refs":[]}
  result=run(self.cases[0],"B4_knowledge",model=mock,history=self.history)
  self.assertGreater(len(result["knowledge_hits"]),0)
 def test_summary(self):
  r=run(self.cases[0],"B1_fixed")
  r.update(evaluate(r,self.gold[self.cases[0]["id"]]))
  self.assertEqual(summarize([r])[0]["n"],1)
