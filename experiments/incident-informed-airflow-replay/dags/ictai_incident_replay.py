"""Optional Airflow 2.7+/3 DAG. Local fixture paths must exist on the worker.

Core logic is tested without a scheduler. This DAG itself requires an Airflow
installation and has not been scheduler-tested in the supplied workspace.
"""
from datetime import datetime, timezone
import os
from airflow.decorators import dag, task


@dag(dag_id='ictai_incident_replay',schedule=None,
     start_date=datetime(2024,1,1,tzinfo=timezone.utc),catchup=False,
     params={'case_id':'01'},tags=['ictai','local-replay'])
def incident_replay():
    @task(retries=0)
    def execute(case_id):
        from pathlib import Path
        from ictai_replay.core import ingest
        # The operator must generate/configure this directory before triggering.
        # Never regenerate fixtures here: doing so would overwrite evidence.
        base=Path(os.environ['ICTAI_REPLAY_ROOT']).resolve()
        if case_id not in ['01','02','03','04','05','06']:
            raise ValueError('unsupported case')
        return ingest(base/('case_'+case_id),os.environ.get('ICTAI_REFERENCE_URL'))

    @task(trigger_rule='all_done')
    def review(case_id):
        from pathlib import Path
        from ictai_replay.core import investigate
        base=Path(os.environ['ICTAI_REPLAY_ROOT']).resolve()
        if case_id not in ['01','02','03','04','05','06']:
            raise ValueError('unsupported case')
        return investigate(base/('case_'+case_id),os.environ.get('ICTAI_REFERENCE_URL'))

    case='{{ params.case_id }}'
    execution=execute(case)
    assessment=review(case)
    execution >> assessment


incident_replay()
