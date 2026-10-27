import unittest
from ictai.confirmation_six import confirm_six
from ictai.reasoning_context import propose_with_symptoms
from ictai.controller import Investigation

CASES={
'MISSING_FILE':[('inspect_manifest',{'expected':True}),('check_object_inventory',{'present':False,'count':0})],
'SCHEMA_DRIFT':[('inspect_schema_contract',{'columns':['id']}),('inspect_observed_schema',{'columns':['id','new']})],
'DATA_QUALITY_ANOMALY':[('inspect_quality_rule',{'active':True,'threshold':0,'rule_id':'not_null'}),('inspect_quality_measurement',{'violations':4,'rule_id':'not_null'})],
'PIPELINE_FAILURE':[('inspect_task_execution',{'failed':True,'run_id':'r1'}),('read_run_events',{'execution_error':True,'run_id':'r1'})],
'FRESHNESS_VIOLATION':[('inspect_freshness_sla',{'active':True,'deadline_epoch':100,'dataset_id':'d1'}),('inspect_arrival_timestamps',{'arrival_epoch':120,'dataset_id':'d1'})],
'DEPENDENCY_FAILURE':[('query_lineage',{'depends_on_upstream':True,'upstream_id':'u1'}),('check_upstream_health',{'healthy':False,'upstream_id':'u1'}),('read_run_events',{'blocked_by_upstream':True,'upstream_id':'u1'})],
}
def ev(pairs): return [{'tool':t,'result':v} for t,v in pairs]
class SixCategoryTests(unittest.TestCase):
    def test_each_category(self):
        for cat, pairs in CASES.items():
            with self.subTest(cat=cat):
                result=confirm_six(ev(pairs),dict(pairs))
                self.assertEqual((result.status,result.category),('CONFIRMED',cat))
                self.assertEqual(len(result.evidence_refs),len(pairs))
    def test_incomplete_abstains(self):
        for cat,pairs in CASES.items():
            with self.subTest(cat=cat): self.assertEqual(confirm_six(ev(pairs[:-1])).status,'ABSTAINED')
    def test_contradiction_reviews(self):
        pairs=CASES['MISSING_FILE']
        result=confirm_six(ev(pairs+[('check_object_inventory',{'present':True,'count':1})]))
        self.assertEqual(result.status,'REVIEW_REQUIRED')
    def test_multiple_candidates_reviews(self):
        result=confirm_six(ev(CASES['MISSING_FILE']+CASES['SCHEMA_DRIFT']))
        self.assertEqual(result.status,'REVIEW_REQUIRED')
    def test_pending_tools_provisional(self):
        pairs=CASES['MISSING_FILE']; tools=dict(pairs);tools['inspect_observed_schema']=lambda:None
        self.assertEqual(confirm_six(ev(pairs),tools,exhausted=False).status,'PROVISIONAL_RCA')
    def test_symptom_prompt_and_validation(self):
        ctx=Investigation('case')
        def fake(messages):
            self.assertIn('delivery alert',messages[1]['content'])
            self.assertNotIn('ground_truth',messages[1]['content'])
            return {'next_layer':'source','hypotheses':[],'open_questions':[],'evidence_refs':[]}
        p=propose_with_symptoms(ctx,{'inspect_manifest':lambda:None},fake,'delivery alert')
        self.assertTrue(p.accepted)
    def test_invalid_symptoms(self):
        with self.assertRaises(ValueError): propose_with_symptoms(Investigation('x'),{},lambda _:None,'')
if __name__=='__main__':unittest.main()
