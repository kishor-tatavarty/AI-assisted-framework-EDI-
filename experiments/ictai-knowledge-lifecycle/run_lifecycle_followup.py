"""Offline follow-up knowledge-use integration test. No network/API calls."""
import json
from ictai.semantic58 import run

BASE_HISTORY = {
    'source_incident_id':'synthetic-2026-incident', 'source_system':'synthetic-testbed',
    'reviewer_id':'synthetic-reviewer', 'verified_at':'2026-01-01T00:00:00Z',
    'valid_from':'2026-01-01T00:00:00Z','valid_until':'2027-01-01T00:00:00Z',
    'layer':'source','description':'Supplier extract source inventory pipeline failure investigation',
    'verified':True,'stale':False,
}
CASE = {
 'id':'offline-followup',
 'symptoms':'Supplier extract source inventory pipeline failure investigation',
 'tools':{
   'inspect_manifest':{'expected':True},
   'check_object_inventory':{'present':True,'count':1},
   'inspect_task_execution':{'failed':True,'run_id':'run-42'},
   'read_run_events':{'execution_error':True,'run_id':'run-42'},
 }
}

def exercise():
    history=[
        {**BASE_HISTORY,'id':'history-supported',
         'expected_current_observations':[{'tool':'check_object_inventory','key':'present','equals':True}]},
        {**BASE_HISTORY,'id':'history-contradicted',
         'expected_current_observations':[{'tool':'check_object_inventory','key':'present','equals':False}]},
    ]
    prompts=[]
    def mock(messages):
        payload=json.loads(messages[-1]['content'])
        ids=[r['id'] for r in payload['retrieved_knowledge']]
        prompts.append({'knowledge_ids':ids,'evidence_count':len(payload['evidence']),
                        'available_layers':payload['available_layers']})
        layer='source' if not payload['visited'] else 'pipeline'
        return json.dumps({'next_layer':layer,'hypotheses':[], 'open_questions':[],
                           'evidence_refs':[], 'knowledge_refs':ids})
    result=run(CASE,'B4_knowledge',model=mock,history=history,budget=12)
    transitions=[{'id':e['record_id'],'from':e['previous_status'],'to':e['status'],
                  'evidence_count':e['evidence_count']} for e in result['knowledge_assessments']]
    assert len(prompts)>=2, ('Need a second model decision',prompts,result)
    assert prompts[0]['knowledge_ids']==[],prompts
    assert prompts[1]['knowledge_ids']==['history-supported'],prompts
    assert [e['to'] for e in transitions if e['id']=='history-supported']==['PENDING','ACCEPTED'],transitions
    assert [e['to'] for e in transitions if e['id']=='history-contradicted']==['PENDING','REJECTED'],transitions
    assert result['status']=='CONFIRMED' and result['prediction']=='PIPELINE_FAILURE',result
    assert all('history-contradicted' not in p['knowledge_ids'] for p in prompts)
    proposals=[e for e in result['audit'] if e.get('event')=='llm_proposal']
    assert proposals[1]['accepted'] and proposals[1]['knowledge_refs']==['history-supported'],proposals
    print(json.dumps({'transitions':transitions,'model_prompts':prompts,
                      'second_proposal_accepted_refs':proposals[1]['knowledge_refs'],
                      'status':result['status'],'prediction':result['prediction']},indent=2))
    print('OFFLINE FOLLOW-UP KNOWLEDGE USE: PASS (2 model decisions; no API calls)')
if __name__=='__main__': exercise()
