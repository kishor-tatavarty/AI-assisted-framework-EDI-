import unittest
from ictai.controller import Investigation
from ictai.rca import classify_root_cause, investigate_and_classify

def ctx(*entries):
    return Investigation('arbitrary-id', evidence=[{'layer':'any','tool':tool,'result':result} for tool,result in entries])

class RCATests(unittest.TestCase):
    def test_missing_file(self):
        r=classify_root_cause(ctx(('inspect_manifest',{'expected':True}),('check_object_inventory',{'count':0})))
        self.assertEqual(r.category,'MISSING_FILE'); self.assertEqual(len(r.evidence_refs),2)
    def test_schema_drift(self):
        r=classify_root_cause(ctx(('inspect_schema_contract',{'columns':['id','amount']}),('inspect_observed_schema',{'columns':['id','total']})))
        self.assertEqual(r.category,'SCHEMA_DRIFT')
    def test_matching_schema_abstains(self):
        r=classify_root_cause(ctx(('inspect_schema_contract',{'columns':['id']}),('inspect_observed_schema',{'columns':['id']})))
        self.assertEqual(r.category,'INSUFFICIENT_EVIDENCE')
    def test_manifest_alone_abstains(self):
        self.assertEqual(classify_root_cause(ctx(('inspect_manifest',{'expected':True}))).status,'ABSTAINED')
    def test_conflicting_inventory_abstains(self):
        r=classify_root_cause(ctx(('inspect_manifest',{'expected':True}),('check_object_inventory',{'count':0,'present':True})))
        self.assertEqual(r.status,'REVIEW_REQUIRED')
    def test_both_causes_require_review(self):
        r=classify_root_cause(ctx(('inspect_manifest',{'expected':True}),('check_object_inventory',{'count':0}),('inspect_schema_contract',{'columns':['a']}),('inspect_observed_schema',{'columns':['b']})))
        self.assertEqual(r.status,'REVIEW_REQUIRED')
    def test_wrong_signal_does_not_change_rca(self):
        tools={'inspect_manifest':lambda:{'expected':True},'check_object_inventory':lambda:{'count':0}}
        _,r=investigate_and_classify('id','schema_drift',tools)
        self.assertEqual(r.category,'MISSING_FILE')
    def test_tool_error_does_not_fabricate_evidence(self):
        def fail():raise RuntimeError('failure')
        _,r=investigate_and_classify('id','missing_file',{'inspect_manifest':lambda:{'expected':True},'check_object_inventory':fail})
        self.assertEqual(r.category,'INSUFFICIENT_EVIDENCE')
    def test_repeated_conflicting_manifest(self):
        r=classify_root_cause(ctx(('inspect_manifest',{'expected':True}),('inspect_manifest',{'expected':False}),('check_object_inventory',{'count':0})))
        self.assertEqual(r.status,'REVIEW_REQUIRED')
    def test_evidence_source_ignores_layer(self):
        r=classify_root_cause(ctx(('inspect_manifest',{'expected':True}),('check_object_inventory',{'present':False})))
        self.assertEqual(r.category,'MISSING_FILE')
if __name__=='__main__':unittest.main()
