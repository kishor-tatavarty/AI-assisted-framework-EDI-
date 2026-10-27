import unittest
from datetime import datetime,timezone
from ictai.knowledge_guard import assess_history
from ictai.semantic58 import run

class LifecycleTests(unittest.TestCase):
 def setUp(self):
  self.r=dict(id="history-1",source_incident_id="fixture-1",source_system="synthetic",reviewer_id="review-fixture",verified_at="2026-01-01T00:00:00Z",valid_from="2026-01-01T00:00:00Z",valid_until="2027-01-01T00:00:00Z",layer="source",description="Supplier extract missing from source object inventory",verified=True,stale=False,expected_current_observations=[dict(tool="check_object_inventory",key="present",equals=False)])
  self.now=datetime(2026,10,26,tzinfo=timezone.utc)
 def test_pending_then_accepted(self):
  self.assertEqual(assess_history(self.r,now=self.now)["status"],"PENDING")
  self.assertEqual(assess_history(self.r,[dict(tool="check_object_inventory",result={"present":False})],now=self.now)["status"],"ACCEPTED")
 def test_pending_then_rejected(self):
  self.assertEqual(assess_history(self.r,[dict(tool="check_object_inventory",result={"present":True})],now=self.now)["status"],"REJECTED")
 def test_no_checks_are_accepted_with_valid_provenance(self):
  r={**self.r,"expected_current_observations":[]}
  self.assertEqual(assess_history(r,now=self.now)["status"],"ACCEPTED")
 def test_lifecycle_audit_and_no_premature_knowledge_prompt(self):
  case={"id":"test-lifecycle","symptoms":"Supplier extract missing from source object inventory","tools":{"inspect_manifest":{"expected":True},"check_object_inventory":{"present":False,"count":0}}}
  prompts=[]
  def model(messages):
   prompts.append(messages)
   return '{"next_layer":"source","hypotheses":[],"open_questions":[],"evidence_refs":[],"knowledge_refs":[]}'
  row=run(case,"B4_knowledge",model=model,history=[self.r],budget=12)
  statuses=[x["status"] for x in row["knowledge_assessments"]]
  self.assertEqual(statuses,["PENDING","ACCEPTED"])
  self.assertTrue(prompts)
  self.assertEqual(row["knowledge_hits"][0]["id"],"history-1")
  self.assertEqual(row["knowledge_assessments"][1]["previous_status"],"PENDING")
