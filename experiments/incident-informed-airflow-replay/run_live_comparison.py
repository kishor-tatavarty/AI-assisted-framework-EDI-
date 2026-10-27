"""Paired four-policy replay; no model is given the test answer key."""
import argparse
import hashlib
import json
from pathlib import Path
from ictai_replay.core import ingest,investigate,write_json
from ictai_replay.scenarios import build,ACCOUNT_SUMMARY
from ictai_replay.service import reference_service
from ictai_replay.llm import load_key,LiveModel,investigate_llm


HISTORY=[
 {'id':'guide-delivery','record_type':'synthetic_design_guidance','text':'For missing file delivery or missing raw rows, check the expected delivery deadline, exact inventory path and access. An absent source input may explain a downstream load failure.'},
 {'id':'guide-columns','record_type':'synthetic_design_guidance','text':'For column or parser errors, compare observed file structure with the approved schema contract before changing a load mapping.'},
 {'id':'guide-values','record_type':'synthetic_design_guidance','text':'For invalid revenue or numeric values, inspect the value contract and failing samples. Matching column count does not establish valid data types.'},
 {'id':'guide-period','record_type':'synthetic_design_guidance','text':'For incorrect converted amounts, check effective month of rates and trace the selected reference rate. A successful load can publish stale reference values.'},
 {'id':'guide-worker','record_type':'synthetic_design_guidance','text':'For job or all fact loads failing while source rows exist, inspect processing task errors and runtime dependencies before assuming a missing input.'},
 {'id':'guide-upstream','record_type':'synthetic_design_guidance','text':'For inventory job failures, verify the upstream reference dependency and link service health to the affected task. Zero rows alone do not identify an upstream cause.'},
]


def main():
    p=argparse.ArgumentParser();p.add_argument('--env-file');p.add_argument('--output',default='results/live_comparison')
    args=p.parse_args();output=Path(args.output);output.mkdir(parents=True,exist_ok=True)
    model=LiveModel(load_key(args.env_file))
    configs=[]
    for case_id in ACCOUNT_SUMMARY:
        configs.append(build(output/f'case_{case_id}',case_id))
    write_json(output/'knowledge.json',HISTORY)
    manifest={'case_config_sha256':{c['id']:hashlib.sha256(json.dumps(c,sort_keys=True).encode()).hexdigest() for c in configs},
              'knowledge_sha256':hashlib.sha256(json.dumps(HISTORY,sort_keys=True).encode()).hexdigest(),
              'model':model.model,'max_model_calls_per_case_per_llm_arm':4,'maximum_total_model_calls':48,
              'all_policies_collect_same_six_domains':True,'no_gold_labels_in_model_input':True,
              'history_type':'synthetic design guidance; not independent verified incident history',
              'scope':'incident-informed generated local replay; one run per policy per case'}
    write_json(output/'manifest.json',manifest)
    rows=[]
    for cfg in configs:
        case_id=cfg['id'];root=output/f'case_{case_id}'
        with reference_service(healthy=False) as endpoint:
            try:ingest(root,endpoint)
            except (FileNotFoundError,ValueError,ImportError,RuntimeError):pass
            for policy in ['fixed','dynamic']:
                row=investigate(root,endpoint,policy);row['llm_attempts']=0
                rows.append(row)
            for knowledge_enabled in [False,True]:
                row=investigate_llm(root,endpoint,model,HISTORY,knowledge_enabled)
                rows.append(row)
                write_json(output/'results.json',rows)
                write_json(output/'model_records.json',model.records)
                print(json.dumps({'case':case_id,'policy':row['policy'],'status':row['status'],
                                  'category':row['category'],'llm_attempts':row['llm_attempts'],
                                  'api_failures':row['api_failures']}),flush=True)
    write_json(output/'results.json',rows)
    write_json(output/'model_records.json',model.records)
    print('LIVE_COMPARISON_COMPLETE',flush=True)


if __name__=='__main__':main()
