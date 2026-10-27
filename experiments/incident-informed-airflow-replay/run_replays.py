"""Run local tasks plus evidence inspection on six adapted scenarios."""
import argparse
import json
from pathlib import Path
from ictai_replay.scenarios import build, ACCOUNT_SUMMARY
from ictai_replay.service import reference_service
from ictai_replay.core import ingest, investigate, write_json


def run_all(output, recovered=False):
    output=Path(output);rows=[]
    for case_id in ACCOUNT_SUMMARY:
        root=output/('case_'+case_id)
        build(root,case_id,recovered=recovered)
        with reference_service(healthy=recovered) as endpoint:
            try:ingest(root,endpoint)
            except (FileNotFoundError,ValueError,ImportError,RuntimeError):pass
            for policy in ['fixed','dynamic']:
                result=investigate(root,endpoint,policy=policy)
                result['recovered_fixture']=recovered
                rows.append(result)
    write_json(output/'results.json',rows)
    write_json(output/'summary.json',[{k:r[k] for k in ['case_id','policy','category','status','tool_attempts','elapsed_ms']} for r in rows])
    return rows


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',default='results/failures')
    p.add_argument('--recovered',action='store_true');args=p.parse_args()
    rows=run_all(args.output,args.recovered)
    print(json.dumps([{k:r[k] for k in ['case_id','policy','category','status','tool_attempts']} for r in rows],indent=2))
