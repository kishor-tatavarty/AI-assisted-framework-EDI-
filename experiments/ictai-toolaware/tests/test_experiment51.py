import unittest
from ictai.experiment import cases
from ictai.experiment51 import run_experiment, run_case, summarize

class Phase51Tests(unittest.TestCase):
    def test_all_arms_paired(self):
        rows=run_experiment()
        self.assertEqual(len(rows),len(cases())*3)
        self.assertEqual({r['arm'] for r in rows},{'B1_fixed','B2_dynamic','B3_knowledge'})
    def test_stops_after_two_missing_file_tools(self):
        case=next(c for c in cases() if c.case_id=='MF01')
        for arm in ('B1_fixed','B2_dynamic','B3_knowledge'):
            ctx,rca,_,_=run_case(case,arm)
            self.assertEqual(rca.category,'MISSING_FILE')
            self.assertEqual(sum('step' in x for x in ctx.audit),2)
            self.assertEqual(ctx.status,'EVIDENCE_SUFFICIENT')
    def test_no_premature_abstention_stop(self):
        case=next(c for c in cases() if c.case_id=='AB01')
        ctx,rca,_,_=run_case(case,'B2_dynamic')
        self.assertEqual(rca.category,'INSUFFICIENT_EVIDENCE')
        self.assertNotEqual(ctx.status,'EVIDENCE_SUFFICIENT')
    def test_conflicting_causes_require_review(self):
        case=next(c for c in cases() if c.case_id=='AB04')
        ctx,rca,_,_=run_case(case,'B1_fixed',max_calls=4)
        self.assertEqual(rca.status,'CLASSIFIED') # stops at missing file before contradictory schema observed
        self.assertEqual(rca.category,'MISSING_FILE')
    def test_budget(self):
        self.assertTrue(all(x['tool_calls']<=3 for x in run_experiment()))
    def test_summary(self):
        self.assertEqual(len(summarize(run_experiment())),3)
if __name__=='__main__': unittest.main()
