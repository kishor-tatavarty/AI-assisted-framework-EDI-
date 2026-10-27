import unittest, json
from ictai.controller import Investigation
from ictai.reasoning_context import propose_with_symptoms,_eligible_layers
class ToolAwareTests(unittest.TestCase):
 def test_extra_tools_eligible(self):
  c=Investigation("x")
  self.assertIn("lineage",_eligible_layers(c,{"query_lineage":lambda:None}))
 def test_visited_excluded(self):
  c=Investigation("x");c.visited.append("source")
  self.assertNotIn("source",_eligible_layers(c,{"inspect_manifest":lambda:None}))
 def test_prompt_excludes_empty_layers(self):
  c=Investigation("x");seen=[]
  def model(messages):
   payload=json.loads(messages[1]["content"]);seen.append(payload)
   return {"next_layer":"source","hypotheses":[],"open_questions":[],"evidence_refs":[],"knowledge_refs":[]}
  p=propose_with_symptoms(c,{"inspect_manifest":lambda:None},model,"missing extract")
  self.assertTrue(p.accepted)
  self.assertEqual(seen[0]["available_layers"],["source"])
  self.assertEqual(seen[0]["eligible_tools_by_layer"]["source"],["inspect_manifest"])
 def test_no_gold_in_prompt(self):
  c=Investigation("x");seen=[]
  def model(messages):
   seen.append(messages[1]["content"])
   return {"next_layer":"source","hypotheses":[],"open_questions":[],"evidence_refs":[],"knowledge_refs":[]}
  propose_with_symptoms(c,{"inspect_manifest":lambda:None},model,"delivery pending")
  self.assertNotIn("ground_truth",seen[0])
