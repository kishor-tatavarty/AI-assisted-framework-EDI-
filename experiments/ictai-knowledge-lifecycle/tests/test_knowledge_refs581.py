import unittest, json
from ictai.controller import Investigation
from ictai.llm_reasoner import validate_proposal
from ictai.reasoning_context import propose_with_symptoms
from ictai.semantic58 import run
GOOD={"next_layer":"source","hypotheses":[],"open_questions":[],"evidence_refs":[],"knowledge_refs":["hist-1"]}
TOOLS={"inspect_manifest":lambda:{"expected":True},"check_object_inventory":lambda:{"present":False}}
H=[{"id":"hist-1","description":"Vendor export held","layer":"source","verified":True,"stale":False,"source_incident_id":"synthetic-1","source_system":"fixture","reviewer_id":"fixture","verified_at":"2026-10-01T00:00:00Z","valid_from":"2026-10-01T00:00:00Z","valid_until":"2027-10-01T00:00:00Z"}]
class KnowledgeRefTests(unittest.TestCase):
 def test_valid_history(self):
  p=validate_proposal(GOOD,Investigation('x'),TOOLS,H)
  self.assertTrue(p.accepted);self.assertEqual(p.knowledge_refs,("hist-1",))
 def test_unknown_history(self):
  self.assertEqual(validate_proposal(GOOD,Investigation('x'),TOOLS,[]).reason,"unverified_knowledge_reference")
 def test_stale_history(self):
  self.assertEqual(validate_proposal(GOOD,Investigation('x'),TOOLS,[{**H[0],"stale":True}]).reason,"unverified_knowledge_reference")
 def test_unverified_history(self):
  self.assertEqual(validate_proposal(GOOD,Investigation('x'),TOOLS,[{**H[0],"verified":False}]).reason,"unverified_knowledge_reference")
 def test_history_in_current_refs_normalized(self):
  p=validate_proposal({**GOOD,"evidence_refs":["hist-1"]},Investigation('x'),TOOLS,H)
  self.assertTrue(p.accepted)
  self.assertEqual(p.evidence_refs,())
  self.assertEqual(p.knowledge_refs,("hist-1",))
  self.assertEqual(p.normalized_refs,("hist-1",))
 def test_legacy_proposal_valid(self):
  self.assertTrue(validate_proposal({k:v for k,v in GOOD.items() if k!="knowledge_refs"},Investigation('x'),TOOLS).accepted)
 def test_structured_prompt(self):
  seen=[]
  def model(messages):
   payload=json.loads(messages[-1]['content']);seen.append(payload)
   return GOOD
  p=propose_with_symptoms(Investigation('x'),TOOLS,model,"Input delivery delayed",retrieved_knowledge=H)
  self.assertTrue(p.accepted)
  self.assertEqual(seen[0]['retrieved_knowledge'][0]['id'],'hist-1')
  self.assertNotIn('hist-1',json.dumps(seen[0]['evidence']))
 def test_b4_accepted_and_audited(self):
  def model(messages):
   payload=json.loads(messages[-1]['content'])
   return {**GOOD,"knowledge_refs":[payload['retrieved_knowledge'][0]['id']]}
  case={"id":"x","symptoms":"Vendor export held", "tools":{"inspect_manifest":{"expected":True},"check_object_inventory":{"present":False}}}
  r=run(case,'B4_knowledge',model=model,history=H)
  self.assertEqual(r['llm_failures'],0)
  self.assertTrue(any(a.get('accepted') and a.get('knowledge_refs')==['hist-1'] for a in r['audit']))
 def test_history_cannot_confirm(self):
  def model(messages):return GOOD
  case={"id":"x","symptoms":"Vendor export held","tools":{"inspect_manifest":{"expected":True}}}
  r=run(case,'B4_knowledge',model=model,history=H)
  self.assertNotEqual(r['status'],'CONFIRMED')
