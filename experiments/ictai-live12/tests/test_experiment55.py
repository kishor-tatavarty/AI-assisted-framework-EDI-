import unittest
from ictai.experiment55 import investigate_six

class EndToEndSix(unittest.TestCase):
    def test_six_categories(self):
        cases=[
          ('missing delivery',{'inspect_manifest':{'expected':True},'check_object_inventory':{'present':False,'count':0}},'MISSING_FILE'),
          ('schema column changed',{'inspect_schema_contract':{'columns':['id']},'inspect_observed_schema':{'columns':['id','new']}},'SCHEMA_DRIFT'),
          ('invalid quality records',{'inspect_quality_rule':{'active':True,'rule_id':'r','threshold':0},'inspect_quality_measurement':{'rule_id':'r','violations':2}},'DATA_QUALITY_ANOMALY'),
          ('dag task failed',{'inspect_task_execution':{'failed':True,'run_id':'a'},'read_run_events':{'execution_error':True,'run_id':'a'}},'PIPELINE_FAILURE'),
          ('late freshness arrival',{'inspect_freshness_sla':{'active':True,'deadline_epoch':10,'dataset_id':'d'},'inspect_arrival_timestamps':{'arrival_epoch':20,'dataset_id':'d'}},'FRESHNESS_VIOLATION'),
          ('upstream dependency failed',{'query_lineage':{'depends_on_upstream':True,'upstream_id':'u'},'check_upstream_health':{'healthy':False,'upstream_id':'u'},'read_run_events':{'blocked_by_upstream':True,'upstream_id':'u'}},'DEPENDENCY_FAILURE'),
        ]
        for symptom, values, expected in cases:
            with self.subTest(expected=expected):
                tools={k:(lambda v=v:v) for k,v in values.items()}
                ctx,dec=investigate_six('case',symptom,tools)
                self.assertEqual((dec.status,dec.category),('CONFIRMED',expected))
                self.assertTrue(dec.evidence_refs)
    def test_no_evidence_abstains(self):
        _,d=investigate_six('a','unknown symptom',{})
        self.assertEqual(d.status,'ABSTAINED')
    def test_conflicting_causes_escalate(self):
        vals={'inspect_manifest':{'expected':True},'check_object_inventory':{'present':False,'count':0},'inspect_schema_contract':{'columns':['a']},'inspect_observed_schema':{'columns':['b']}}
        _,d=investigate_six('c','missing file schema error',{k:(lambda v=v:v) for k,v in vals.items()})
        self.assertEqual(d.status,'REVIEW_REQUIRED')
    def test_llm_proposal_is_used(self):
        vals={'inspect_manifest':{'expected':True},'check_object_inventory':{'present':False,'count':0}}
        def model(messages):
            return {'next_layer':'source','hypotheses':[],'open_questions':[],'evidence_refs':[]}
        ctx,d=investigate_six('x','data not delivered',{k:(lambda v=v:v) for k,v in vals.items()},model)
        self.assertEqual(d.status,'CONFIRMED')
        self.assertTrue(any(x.get('event')=='llm_proposal' and x.get('accepted') for x in ctx.audit))
if __name__=='__main__': unittest.main()
