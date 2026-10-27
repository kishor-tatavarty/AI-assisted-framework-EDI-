import unittest
from ictai_replay.llm import validate_route,validate_diagnosis,retrieve


class ValidationTests(unittest.TestCase):
    def test_future_evidence_reference_rejected(self):
        p={'next_tools':['source','tables'],'reason':'check inputs','evidence_refs':['execution'],'knowledge_refs':[]}
        self.assertFalse(validate_route(p,['source','tables'],[],[])[0])

    def test_duplicate_tools_rejected(self):
        p={'next_tools':['source','source'],'reason':'check','evidence_refs':[],'knowledge_refs':[]}
        self.assertFalse(validate_route(p,['source','tables'],[],[])[0])

    def test_history_cannot_be_current_evidence(self):
        p={'category':'MISSING_FILE','rationale':'missing','recommendation':'review',
           'missing_checks':[],'evidence_refs':['guide-delivery'],'knowledge_refs':[]}
        self.assertFalse(validate_diagnosis(p,[{'tool':'source'}],[{'id':'guide-delivery'}])[0])

    def test_valid_proposal_and_empty_history(self):
        p={'category':'MISSING_FILE','rationale':'missing','recommendation':'review',
           'missing_checks':[],'evidence_refs':['source'],'knowledge_refs':[]}
        self.assertTrue(validate_diagnosis(p,[{'tool':'source'}],[])[0])
        self.assertEqual(retrieve('an unrelated symptom',[]),[])

    def test_non_string_category_rejected(self):
        self.assertFalse(validate_diagnosis({'category':[]},[],[])[0])


if __name__=='__main__':unittest.main()
