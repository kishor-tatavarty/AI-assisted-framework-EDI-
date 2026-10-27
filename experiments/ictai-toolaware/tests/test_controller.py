import unittest
from ictai.controller import investigate

class ControllerTests(unittest.TestCase):
    def test_budget(self):
        tools = {"inspect_manifest":lambda: {"present":False}, "check_object_inventory":lambda: {"count":0}}
        x = investigate("missing-01", tools, max_calls=1)
        self.assertEqual(x.status,"BUDGET_EXHAUSTED")
        self.assertEqual(len(x.evidence),1)
    def test_schema(self):
        tools = {"inspect_schema_contract":lambda:{"columns":["id"]},"inspect_observed_schema":lambda:{"columns":["id","new"]}}
        x = investigate("schema-01",tools,priority=("validation",))
        self.assertEqual(x.status,"EVIDENCE_COLLECTED")
        self.assertEqual(len(x.evidence),2)
    def test_abstain(self):
        x=investigate("none",{},priority=("source",))
        self.assertEqual(x.status,"INSUFFICIENT_EVIDENCE")

if __name__=='__main__': unittest.main()
