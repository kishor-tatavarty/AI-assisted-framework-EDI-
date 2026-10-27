import unittest
from unittest.mock import patch
from ictai.semantic58 import run

class ObservabilityTests(unittest.TestCase):
    def setUp(self):
        self.case={"id":"obs-test","symptoms":"source file missing","tools":{
          "inspect_manifest":{"expected":True,"run_id":"obs-test"},
          "check_object_inventory":{"present":False,"count":0,"run_id":"obs-test"}}}
    def test_success_accounting(self):
        result=run(self.case,"B1_fixed")
        audit=result["audit"]
        attempts=[x for x in audit if x["event"]=="tool_attempt"]
        successes=[x for x in audit if x["event"]=="tool_success"]
        self.assertEqual(result["attempted_tool_calls"],len(attempts))
        self.assertEqual(result["successful_observations"],len(successes))
        self.assertEqual(result["failed_tool_calls"],0)
        self.assertEqual(result["tool_calls"],result["attempted_tool_calls"])
        self.assertTrue(any(x["event"]=="confirmation_checkpoint" for x in audit))
        self.assertEqual(audit[-1]["event"],"confirmation_final")
    def test_failed_tool_accounting(self):
        with patch("ictai.semantic58.confirm_six") as confirm:
            class D:
                status="INVESTIGATING";category="INSUFFICIENT_EVIDENCE";evidence_refs=[]
            confirm.return_value=D()
            with patch("ictai.semantic58.LAYERS",{"source":["inspect_manifest"]}),patch("ictai.semantic58.ORDER",["source"]),patch("ictai.semantic58._eligible_layers",return_value=["source"]):
                # A non-mapping result causes dict(v) to raise during tool invocation.
                case={"id":"failed","symptoms":"missing source file","tools":{"inspect_manifest":42}}
                result=run(case,"B1_fixed")
                self.assertEqual(result["attempted_tool_calls"],1)
                self.assertEqual(result["successful_observations"],0)
                self.assertEqual(result["failed_tool_calls"],1)
                self.assertEqual(len([x for x in result["audit"] if x["event"]=="tool_error"]),1)
