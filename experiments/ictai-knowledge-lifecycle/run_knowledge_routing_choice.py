"""Offline counterfactual knowledge-routing diagnostic; mock models, no API."""
import json
from ictai.semantic58 import run

BASE={
 'source_incident_id':'synthetic-history-01','source_system':'synthetic-testbed',
 'reviewer_id':'fixture-reviewer','verified_at':'2026-01-01T00:00:00Z',
 'valid_from':'2026-01-01T00:00:00Z','valid_until':'2027-01-01T00:00:00Z',
 'verified':True,'stale':False,
}
SCENARIOS=[
 {'name':'schema_migration','id':'routing-schema','symptoms':'Partner deployment parser rejects unexpected attributes after source delivery',
  'history_layer':'validation','history_desc':'Partner deployment parser rejects unexpected attributes; check schema migration contract',
  'tools':{'inspect_manifest':{'expected':True},'check_object_inventory':{'present':True,'count':1},
           'inspect_schema_contract':{'columns':['customer_key']},'inspect_observed_schema':{'columns':['account_key']},
           'inspect_task_execution':{'failed':False,'run_id':'run-1'},'read_run_events':{'execution_error':False,'run_id':'run-1'}}},
 {'name':'upstream_dependency','id':'routing-dependency','symptoms':'Reference endpoint timeout blocked enrichment feed after scheduled input arrived',
  'history_layer':'lineage','history_desc':'Reference endpoint timeout blocked enrichment feed; inspect upstream dependency lineage',
  'tools':{'inspect_manifest':{'expected':True},'check_object_inventory':{'present':True,'count':1},
           'inspect_task_execution':{'failed':False,'run_id':'run-2'},'read_run_events':{'execution_error':False,'run_id':'run-2','blocked_by_upstream':True,'upstream_id':'ref-1'},
           'check_upstream_health':{'healthy':False,'upstream_id':'ref-1'},'query_lineage':{'depends_on_upstream':True,'upstream_id':'ref-1'}}}
]

def run_case(s):
    history=[{**BASE,'id':'history-'+s['name'],'layer':s['history_layer'],
       'description':s['history_desc'],
       'expected_current_observations':[{'tool':'check_object_inventory','key':'present','equals':True}]}]
    case={k:s[k] for k in ('id','symptoms','tools')}
    prompts={}
    def make_mock(arm):
        prompts[arm]=[]
        def mock(messages):
            payload=json.loads(messages[-1]['content'])
            ids=[r['id'] for r in payload['retrieved_knowledge']]
            eligible=payload['available_layers']
            prompts[arm].append({'available_layers':eligible,'knowledge_ids':ids,'evidence_count':len(payload['evidence'])})
            # Both start with source; after source, B3 prefers pipeline, B4 uses
            # the eligible knowledge recommendation. This is scripted behavior,
            # not a measured LLM advantage.
            if 'source' in eligible and not payload['visited']:
                layer='source'
            elif ids and s['history_layer'] in eligible:
                layer=s['history_layer']
            elif 'pipeline' in eligible:
                layer='pipeline'
            else:
                layer=eligible[0]
            return json.dumps({'next_layer':layer,'hypotheses':[], 'open_questions':[],
              'evidence_refs':[],'knowledge_refs':ids if ids and layer==s['history_layer'] else []})
        return mock
    results={arm:run(case,arm,model=make_mock(arm),history=history,budget=12)
             for arm in ('B3_llm','B4_knowledge')}
    report={}
    for arm,r in results.items():
        layers=[e['layer'] for e in r['audit'] if e.get('event')=='layer_selected']
        report[arm]={'layers':layers,'relevant_layer_position':layers.index(s['history_layer'])+1 if s['history_layer'] in layers else None,
          'status':r['status'],'prediction':r['prediction'],
          'tool_calls':r['tool_calls'],'knowledge_transitions':[{'from':e.get('previous_status'),'to':e['status']}
          for e in r['knowledge_assessments']],'prompts':prompts[arm],
          'accepted_refs':[e['knowledge_refs'] for e in r['audit'] if e.get('event')=='llm_proposal' and e.get('knowledge_refs')]}
    assert report['B4_knowledge']['knowledge_transitions']==[{'from':None,'to':'PENDING'},{'from':'PENDING','to':'ACCEPTED'}],report
    assert report['B3_llm']['prompts'][0]['knowledge_ids']==[]
    assert report['B4_knowledge']['prompts'][0]['knowledge_ids']==[]
    assert report['B4_knowledge']['prompts'][1]['knowledge_ids']==['history-'+s['name']],report
    assert report['B4_knowledge']['relevant_layer_position'] < report['B3_llm']['relevant_layer_position'],report
    assert report['B4_knowledge']['accepted_refs'],report
    assert report['B3_llm']['prediction']==report['B4_knowledge']['prediction'],report
    return report

if __name__=='__main__':
    results={s['name']:run_case(s) for s in SCENARIOS}
    print(json.dumps(results,indent=2))
    print('OFFLINE KNOWLEDGE ROUTING CHOICE: PASS (2 scenarios, mock models, no API calls)')
