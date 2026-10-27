"""Offline controller integration: synthetic knowledge lifecycle, no API calls."""
import json
from ictai.semantic58 import run

BASE = {
    'id':'offline-lifecycle-fixture',
    'symptoms':'Supplier extract missing from source object inventory',
    'tools':{'inspect_manifest':{'expected':True}, 'check_object_inventory':{'present':False,'count':0}}
}
HISTORY = {
    'id':'history-fixture-01','source_incident_id':'synthetic-incident-01',
    'source_system':'synthetic-fixture','reviewer_id':'synthetic-reviewer',
    'verified_at':'2026-01-01T00:00:00Z','valid_from':'2026-01-01T00:00:00Z',
    'valid_until':'2027-01-01T00:00:00Z','layer':'source',
    'description':'Supplier extract missing from source object inventory',
    'verified':True,'stale':False,
    'expected_current_observations':[{'tool':'check_object_inventory','key':'present','equals':False}]
}

def scenario(name, present, expected):
    case={**BASE,'id':f'offline-{name}', 'tools':{**BASE['tools'],'check_object_inventory':{'present':present,'count':int(present)}}}
    seen=[]
    def mock(messages):
        payload=json.loads(messages[-1]['content'])
        seen.append([h['id'] for h in payload['retrieved_knowledge']])
        return json.dumps({'next_layer':'source','hypotheses':[],'open_questions':[],
                           'evidence_refs':[],'knowledge_refs':[]})
    result=run(case,'B4_knowledge',model=mock,history=[HISTORY],budget=12)
    transitions=[{'from':a['previous_status'],'to':a['status'],'evidence_count':a['evidence_count']} for a in result['knowledge_assessments']]
    actual=[t['to'] for t in transitions]
    assert actual==expected,(name,actual,expected)
    assert seen and all(not refs for refs in seen), 'Pending history entered model prompt prematurely'
    assert result['knowledge_hits']==([] if present else result['knowledge_hits'])
    if not present:assert [x['id'] for x in result['knowledge_hits']]==[HISTORY['id']]
    print(json.dumps({'scenario':name,'transitions':transitions,'llm_prompt_knowledge_ids':seen,
                      'final_history_ids':[h['id'] for h in result['knowledge_hits']],
                      'rca_status':result['status'],'rca_prediction':result['prediction']}))

if __name__=='__main__':
    scenario('matching_current_evidence',False,['PENDING','ACCEPTED'])
    scenario('contradictory_current_evidence',True,['PENDING','REJECTED'])
    print('OFFLINE CONTROLLER INTEGRATION: PASS (2 scenarios; no API calls)')
