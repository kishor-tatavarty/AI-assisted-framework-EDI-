
import unittest
from ictai.controller import investigate_dynamic, select_next_layer

class DynamicTests(unittest.TestCase):
    def test_missing_file_routes_source_first(self):
        x = investigate_dynamic("m1", "missing_file", {
            "inspect_manifest": lambda: {"expected": True, "present": False},
            "check_object_inventory": lambda: {"count": 0},
            "inspect_schema_contract": lambda: {"columns": ["id"]},
        })
        self.assertEqual(x.visited[0], "source")
        self.assertEqual(x.status, "EVIDENCE_COLLECTED")
        self.assertTrue(any(a.get("event") == "layer_selected" for a in x.audit))

    def test_schema_routes_validation_first(self):
        x = investigate_dynamic("s1", "schema_drift", {
            "inspect_schema_contract": lambda: {"columns": ["id"]},
            "inspect_observed_schema": lambda: {"columns": ["id", "new"]},
            "inspect_manifest": lambda: {"present": True},
        })
        self.assertEqual(x.visited[0], "validation")

    def test_budget_is_bounded(self):
        x = investigate_dynamic("m2", "missing_file", {
            "inspect_manifest": lambda: {},
            "check_object_inventory": lambda: {},
        }, max_calls=1)
        self.assertEqual(x.status, "BUDGET_EXHAUSTED")
        self.assertEqual(len(x.evidence), 1)

    def test_unknown_signal_rejected(self):
        with self.assertRaises(ValueError):
            select_next_layer("unknown", [], {})

    def test_no_tools_abstains(self):
        x = investigate_dynamic("none", "missing_file", {})
        self.assertEqual(x.status, "INSUFFICIENT_EVIDENCE")

    def test_evidence_redirects_to_validation(self):
        layer = select_next_layer("missing_file", ["source"], {
            "inspect_schema_contract": lambda: {},
            "inspect_task_execution": lambda: {},
        }, [{"result": {"schema_mismatch": True}}])
        self.assertEqual(layer, "validation")

if __name__ == "__main__":
    unittest.main()
