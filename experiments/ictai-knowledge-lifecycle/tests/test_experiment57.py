import unittest
from ictai.experiment57 import choose_layer,run_case
class TestPilot57(unittest.TestCase):
 def test_fixed_dynamic(self):
  t={'inspect_manifest':lambda:{},'inspect_schema_contract':lambda:{}}
  self.assertEqual(choose_layer('schema column',t,[],'B1_fixed')[0],'source')
  self.assertEqual(choose_layer('schema column',t,[],'B2_dynamic')[0],'validation')
 def test_knowledge_changes_route(self):
  t={'inspect_manifest':lambda:{},'inspect_schema_contract':lambda:{}}
  self.assertEqual(choose_layer('missing file',t,[],'B4_knowledge',knowledge=('validation',))[1],'knowledge')
 def test_gold_not_required(self):
  x=run_case({'id':'x','symptoms':'file missing','tools':{'inspect_manifest':{'expected':True},'check_object_inventory':{'present':False,'count':0}}},'B2_dynamic')
  self.assertEqual(x['prediction'],'MISSING_FILE')
  self.assertNotIn('gold',x)
 def test_model_required(self):
  with self.assertRaises(ValueError):run_case({'id':'x','symptoms':'file','tools':{}},'B3_llm')
