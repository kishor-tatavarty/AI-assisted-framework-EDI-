"""Small live B3/B4 routing experiment; no scripted routing decisions."""
import argparse, json, hashlib
from pathlib import Path
from datetime import datetime, timezone
from run_knowledge_routing_choice import SCENARIOS, BASE
from ictai.semantic58 import run

ROOT=Path(__file__).resolve().parent

def history_for(s):
    return [{**BASE,'id':'history-'+s['name'],'layer':s['history_layer'],
             'description':s['history_desc'],
             'expected_current_observations':[{'tool':'check_object_inventory','key':'present','equals':True}]}]

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--live',action='store_true',help='Make billable OpenAI API calls')
    p.add_argument('--output',default='results/knowledge_routing_live')
    args=p.parse_args()
    cases=[{k:s[k] for k in ('id','symptoms','tools')} for s in SCENARIOS]
    manifest={'cases':[s['name'] for s in SCENARIOS], 'arms':['B3_llm','B4_knowledge'],
              'budget':12,'model':'gpt-4.1-mini (or ICTAI_MODEL override)',
              'fixture_sha256':hashlib.sha256(json.dumps(SCENARIOS,sort_keys=True).encode()).hexdigest(),
              'synthetic':True}
    print('Manifest:',json.dumps(manifest,indent=2))
    if not args.live:
        print('PREVIEW ONLY: pass --live to execute 4 investigations (up to 16 model requests).')
        return
    from dotenv import load_dotenv
    load_dotenv(ROOT/'.env',override=True)
    from ictai.live_openai import OpenAIResponsesAdapter
    model=OpenAIResponsesAdapter()
    rows=[]
    out=ROOT/args.output
    out.parent.mkdir(parents=True,exist_ok=True)
    try:
        for s,case in zip(SCENARIOS,cases):
            for arm in ('B3_llm','B4_knowledge'):
                r=run(case,arm,model=model,history=history_for(s),budget=12)
                layers=[e['layer'] for e in r['audit'] if e.get('event')=='layer_selected']
                target=s['history_layer']
                r['scenario']=s['name']
                r['target_layer']=target
                r['selected_layers']=layers
                r['target_layer_position']=layers.index(target)+1 if target in layers else None
                r['accepted_knowledge_refs']=sorted(set(ref for e in r['audit'] if e.get('event')=='llm_proposal' and e.get('accepted') for ref in e.get('knowledge_refs',[])))
                rows.append(r)
                print(s['name'],arm,'layers',layers,'target_position',r['target_layer_position'],
                      'knowledge_refs',r['accepted_knowledge_refs'],'status',r['status'],
                      'prediction',r['prediction'],'llm_failures',r['llm_failures'],flush=True)
    finally:
        (out.with_name(out.name+'_audit.json')).write_text(json.dumps(rows,indent=2))
        (out.with_name(out.name+'_model_records.json')).write_text(json.dumps(model.records,indent=2))
        (out.with_name(out.name+'_manifest.json')).write_text(json.dumps(manifest,indent=2))
        print('Saved results:',out.parent,flush=True)
    print('Development pilot only. Synthetic histories are not independently verified.')

if __name__=='__main__':main()
