"""Offline, read-only risk-aware stopping counterfactual. Never changes production confirmation."""
import json
from pathlib import Path
from ictai.confirmation_six import confirm_six, CONTRACTS
from ictai.semantic58 import run

ROOT=Path(__file__).resolve().parent
cases=json.loads((ROOT/'stopping_study/baseline_cases.json').read_text())
cases+=json.loads((ROOT/'stopping_study/dependency_variants.json').read_text())

def risk_checkpoint(evidence, available):
    """Conservative closure: all potentially confirmable competing contracts must be observed.

    A category is potentially confirmable when every tool in its contract exists
    in the available tool set. No negative inference from absent tool results.
    """
    observed={e['tool'] for e in evidence}
    available=set(available)
    possible={cat for cat,required in CONTRACTS.items() if set(required)<=available}
    necessary=set().union(*(set(CONTRACTS[c]) for c in possible)) if possible else set()
    local=confirm_six(evidence,available_tools={t:True for t in observed},exhausted=False)
    missing=sorted(necessary-observed)
    if local.status=='REVIEW_REQUIRED':
        return {'status':'REVIEW_REQUIRED','category':local.category,'missing':missing,'possible':sorted(possible)}
    if local.status=='CONFIRMED' and not missing:
        return {'status':'CONFIRMED','category':local.category,'missing':missing,'possible':sorted(possible)}
    return {'status':'INVESTIGATING','category':local.category,'missing':missing,'possible':sorted(possible)}

def replay(case):
    baseline=run(case,'B1_fixed',budget=12)
    successes=[e['tool'] for e in baseline['audit'] if e.get('event')=='tool_success']
    evidence=[];first=None; checkpoints=[]
    for idx,tool in enumerate(successes,1):
        evidence.append({'tool':tool,'result':case['tools'][tool]})
        check=risk_checkpoint(evidence,case['tools'])
        checkpoints.append({'n':idx,'tool':tool,**check})
        if first is None and check['status'] in ('CONFIRMED','REVIEW_REQUIRED'):
            first={'n':idx,'status':check['status'],'category':check['category']}
    strict=(baseline['status'],baseline['prediction'])
    candidate=(first['status'],first['category']) if first else strict
    assert candidate==strict, (case['id'],candidate,strict)
    return {'id':case['id'],'strict_status':strict[0],'strict_category':strict[1],
            'strict_attempts':baseline['tool_calls'],'candidate_first':first,
            'hypothetical_saved_calls':baseline['tool_calls']-first['n'] if first else 0,
            'checkpoints':checkpoints}

def main():
    results=[replay(c) for c in cases]
    # Adversarial: both full schema and pipeline contracts are present; early schema alone cannot stop.
    schema=next(c for c in cases if 'schema_drift' in c['id'])
    tools=dict(schema['tools'])
    tools['inspect_task_execution']={'failed':True,'run_id':'affected-1'}
    tools['read_run_events']={'execution_error':True,'run_id':'affected-1'}
    ev=[{'tool':t,'result':tools[t]} for t in ('inspect_schema_contract','inspect_observed_schema')]
    early=risk_checkpoint(ev,tools)
    assert early['status']=='INVESTIGATING' and 'read_run_events' in early['missing'],early
    ev += [{'tool':t,'result':tools[t]} for t in ('inspect_task_execution','read_run_events')]
    conflict=risk_checkpoint(ev,tools)
    assert conflict['status']=='REVIEW_REQUIRED',conflict
    # A tool not belonging to ANY fully available competing contract is skippable.
    reduced=dict(schema['tools'])
    reduced.pop('read_run_events',None)  # pipeline failure cannot be corroborated
    partial=[{'tool':t,'result':reduced[t]} for t in ('inspect_schema_contract','inspect_observed_schema')]
    safe=risk_checkpoint(partial,reduced)
    assert safe['status']=='CONFIRMED',safe
    output={'results':results,'adversarial':{'early':early,'after_competing_evidence':conflict},
            'partial_tool_inventory':safe,
            'limitations':['Synthetic fixtures only','This assumes a complete, trusted tool inventory',
              'Cannot detect unknown competing causes or faulty tool results',
              'No change to production stopping policy or controller',
              'Does not establish end-to-end savings until integrated and validated']}
    (ROOT/'risk_aware_results.json').write_text(json.dumps(output,indent=2))
    for r in results:
        print(r['id'],r['strict_status'],r['strict_category'],'calls',r['strict_attempts'],
              'risk_first',r['candidate_first']['n'] if r['candidate_first'] else 'none',
              'potential_saved',r['hypothetical_saved_calls'])
    print('ADVERSARIAL: early',early['status'],'final',conflict['status'])
    print('PARTIAL INVENTORY:',safe['status'])
    print('RISK-AWARE STOPPING STUDY: PASS (read-only; no API calls)')
if __name__=='__main__':main()
