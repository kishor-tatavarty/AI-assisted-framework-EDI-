import unittest
from ictai.experiment import cases, run_pilot, summarize, pilot_repo, knowledge_dynamic

class ExperimentTests(unittest.TestCase):
    def test_paired_cases(self):
        rows=run_pilot()
        self.assertEqual(len(rows),len(cases())*3)
        for case in cases():
            self.assertEqual({r['arm'] for r in rows if r['case_id']==case.case_id},
                             {'B1_fixed','B2_dynamic','B3_knowledge'})
    def test_budget(self):
        self.assertTrue(all(r['tool_calls']<=3 for r in run_pilot()))
    def test_no_test_ids_in_knowledge(self):
        self.assertFalse(set(c.case_id for c in cases()) & set(r['id'] for r in pilot_repo().records))
    def test_knowledge_changes_first_layer_when_advice_differs(self):
        case=next(c for c in cases() if c.case_id=='MF02')
        ctx,matches=knowledge_dynamic(case,pilot_repo())
        self.assertEqual(ctx.visited[0],'validation') # schema drift signal, no matching test data
    def test_summary_counts(self):
        self.assertTrue(all(r['n']==len(cases()) for r in summarize(run_pilot())))
