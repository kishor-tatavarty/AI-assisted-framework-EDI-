import unittest
from ictai.controller import Investigation
from ictai.llm_reasoner import validate_proposal, propose
from ictai.experiment53 import investigate_llm

GOOD={'next_layer':'source','hypotheses':['delivery missing'],'open_questions':['Was delivery expected?'],'evidence_refs':[]}
TOOLS={'inspect_manifest':lambda:{'expected':True},'check_object_inventory':lambda:{'present':False}}
class LLMTests(unittest.TestCase):
    def test_valid_proposal(self):
        self.assertTrue(validate_proposal(GOOD,Investigation('x'),TOOLS).accepted)
    def test_invalid_layer(self):
        self.assertFalse(validate_proposal({**GOOD,'next_layer':'admin'},Investigation('x'),TOOLS).accepted)
    def test_fabricated_ref(self):
        self.assertEqual(validate_proposal({**GOOD,'evidence_refs':['evidence[99]/x']},Investigation('x'),TOOLS).reason,'unverified_evidence_reference')
    def test_repeated_layer(self):
        c=Investigation('x'); c.visited.append('source')
        self.assertFalse(validate_proposal(GOOD,c,TOOLS).accepted)
    def test_bad_json(self):
        self.assertFalse(validate_proposal('{oops',Investigation('x'),TOOLS).accepted)
    def test_model_error(self):
        def broken(_): raise RuntimeError('offline')
        self.assertEqual(propose(Investigation('x'),TOOLS,broken).reason,'model_error')
    def test_bounded_and_confirmed(self):
        c,d=investigate_llm('x','missing_file',TOOLS,lambda _:GOOD,max_llm_calls=1)
        self.assertEqual(d.status,'CONFIRMED')
        self.assertEqual(d.category,'MISSING_FILE')
        self.assertLessEqual(sum(a.get('event')=='llm_proposal' for a in c.audit),1)
    def test_invalid_model_falls_back(self):
        c,d=investigate_llm('x','missing_file',TOOLS,lambda _:{'wrong':1},max_llm_calls=1)
        self.assertEqual(d.status,'CONFIRMED')
        self.assertTrue(any(a.get('event')=='fallback' for a in c.audit))
    def test_zero_model_budget(self):
        c,d=investigate_llm('x','missing_file',TOOLS,lambda _:1,max_llm_calls=0)
        self.assertEqual(d.status,'CONFIRMED')
        self.assertFalse(any(a.get('event')=='llm_proposal' for a in c.audit))
    def test_no_tools_abstains(self):
        c,d=investigate_llm('x','missing_file',{},lambda _:GOOD)
        self.assertNotEqual(d.status,'CONFIRMED')
if __name__=='__main__': unittest.main()
