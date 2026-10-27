import unittest
from ictai.controller import Investigation
from ictai.llm_reasoner import validate_proposal
class Normalization582Tests(unittest.TestCase):
 def setUp(self):
  self.ctx=Investigation("incident")
  self.tools={"inspect_manifest":lambda: {}}
  self.knowledge=[{"id":"train-missing_file-0","verified":True,"stale":False},{"id":"old","verified":True,"stale":True},{"id":"unverified","verified":False,"stale":False}]
 def proposal(self,evidence=None,knowledge=None):
  return {"next_layer":"source","hypotheses":[],"open_questions":[],"evidence_refs":evidence or [],"knowledge_refs":knowledge or []}
 def test_known_historical_id_normalizes(self):
  p=validate_proposal(self.proposal(["train-missing_file-0"]),self.ctx,self.tools,self.knowledge)
  self.assertTrue(p.accepted);self.assertEqual(p.evidence_refs,());self.assertEqual(p.knowledge_refs,("train-missing_file-0",));self.assertEqual(p.normalized_refs,("train-missing_file-0",))
 def test_unknown_rejected(self):
  p=validate_proposal(self.proposal(["train-unknown-999"]),self.ctx,self.tools,self.knowledge)
  self.assertFalse(p.accepted);self.assertEqual(p.reason,"unverified_evidence_reference")
 def test_stale_rejected(self):
  self.assertFalse(validate_proposal(self.proposal(["old"]),self.ctx,self.tools,self.knowledge).accepted)
 def test_unverified_rejected(self):
  self.assertFalse(validate_proposal(self.proposal(["unverified"]),self.ctx,self.tools,self.knowledge).accepted)
 def test_mixed_unknown_rejected_atomically(self):
  self.assertFalse(validate_proposal(self.proposal(["train-missing_file-0","made-up"]),self.ctx,self.tools,self.knowledge).accepted)
 def test_current_evidence_kept_separate(self):
  self.ctx.evidence.append({"tool":"inspect_manifest","result":{"expected":True}})
  self.tools["check_object_inventory"]=lambda: {}
  p=validate_proposal(self.proposal(["evidence[0]/inspect_manifest","train-missing_file-0"]),self.ctx,self.tools,self.knowledge)
  self.assertTrue(p.accepted);self.assertEqual(p.evidence_refs,("evidence[0]/inspect_manifest",));self.assertEqual(p.knowledge_refs,("train-missing_file-0",))
 def test_duplicate_normalization_deduplicates(self):
  p=validate_proposal(self.proposal(["train-missing_file-0"],["train-missing_file-0"]),self.ctx,self.tools,self.knowledge)
  self.assertTrue(p.accepted);self.assertEqual(len(p.knowledge_refs),1)
 def test_no_retrieval_cannot_normalize(self):
  self.assertFalse(validate_proposal(self.proposal(["train-missing_file-0"]),self.ctx,self.tools,()).accepted)
 def test_invalid_explicit_knowledge_rejected(self):
  p=validate_proposal(self.proposal([],['old']),self.ctx,self.tools,self.knowledge)
  self.assertFalse(p.accepted);self.assertEqual(p.reason,'unverified_knowledge_reference')
