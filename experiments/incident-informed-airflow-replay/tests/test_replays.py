import tempfile
import unittest
from pathlib import Path
import csv
import json
from contextlib import closing
from ictai_replay.scenarios import build
from ictai_replay.service import reference_service
from ictai_replay.core import ingest, investigate, classify, write_json


class ReplayTests(unittest.TestCase):
    expected={'01':'MISSING_FILE','02':'SCHEMA_DRIFT','03':'DATA_QUALITY_ANOMALY',
              '04':'FRESHNESS_VIOLATION','05':'PIPELINE_FAILURE','06':'DEPENDENCY_FAILURE'}

    def exercise(self,root,case,recovered=False):
        build(root,case,recovered)
        with reference_service(healthy=recovered) as url:
            try:ingest(root,url)
            except Exception:pass
            return [investigate(root,url,policy=p) for p in ['fixed','dynamic']]

    def test_all_failure_mechanisms_and_recoveries(self):
        with tempfile.TemporaryDirectory() as temp:
            for case,category in self.expected.items():
                with self.subTest(case=case):
                    root=Path(temp)/case
                    for result in self.exercise(root,case):
                        self.assertEqual(result['category'],category)
                        self.assertEqual(result['status'],'SUPPORTED_IN_REPLAY')
                        self.assertEqual(result['tool_attempts'],6)
                        self.assertTrue(result['evidence_refs'])
                    for result in self.exercise(root,case,recovered=True):
                        self.assertEqual(result['category'],'NO_INCIDENT')

    def test_no_confirmation_from_zero_rows_alone(self):
        result=classify([{'tool':'tables','result':{'raw_count':0,'fact_count':0}}])
        self.assertEqual(result['status'],'ABSTAINED')

    def test_missing_file_before_deadline_not_confirmed(self):
        r=classify([{'tool':'source','result':{'expected':True,'present':False,
           'delivery_deadline':'2024-01-01T05:00:00-05:00','inspection_time':'2024-01-01T04:00:00-05:00'}}])
        self.assertEqual(r['status'],'ABSTAINED')

    def test_dependency_requires_matching_run_link(self):
        r=classify([{'tool':'dependency','result':{'required':True,'healthy':False,'upstream_id':'a'}},
                   {'tool':'execution','result':{'error_code':'UpstreamUnavailable','upstream_id':'other'}}])
        self.assertEqual(r['status'],'ABSTAINED')

    def test_competing_causes_require_review(self):
        r=classify([{'tool':'validation','result':{'available':True,'schema_mismatch':True}},
                   {'tool':'execution','result':{'status':'FAILED','error_code':'ImportError'}}])
        self.assertEqual(r['status'],'REVIEW_REQUIRED')

    def test_rates_trace_and_reconciliation(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'case'
            failure=self.exercise(root,'04')[0]
            log=json.loads((root/'task_run.json').read_text())
            self.assertEqual(log['selected_rate_month'],'2024-02')
            import sqlite3
            with closing(sqlite3.connect(root/'data.sqlite')) as con:
                self.assertAlmostEqual(con.execute('SELECT converted_revenue FROM fact').fetchone()[0],110)
            self.exercise(root,'04',True)
            log=json.loads((root/'task_run.json').read_text())
            self.assertEqual(log['selected_rate_month'],'2024-03')
            with closing(sqlite3.connect(root/'data.sqlite')) as con:
                self.assertAlmostEqual(con.execute('SELECT converted_revenue FROM fact').fetchone()[0],120)

    def test_failed_numeric_load_has_no_partial_writes(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'case'
            self.exercise(root,'03')
            import sqlite3
            with closing(sqlite3.connect(root/'data.sqlite')) as con:
                self.assertEqual(con.execute('SELECT COUNT(*) FROM raw').fetchone()[0],0)
                self.assertEqual(con.execute('SELECT COUNT(*) FROM fact').fetchone()[0],0)

    def test_no_external_service_allowed(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'case';build(root,'06')
            with self.assertRaises(ValueError):ingest(root,'https://example.com/inventory')


if __name__=='__main__':unittest.main()
