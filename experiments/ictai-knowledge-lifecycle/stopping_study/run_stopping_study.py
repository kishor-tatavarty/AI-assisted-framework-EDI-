"""Read-only comparison of strict and hypothetical category stopping. No API calls."""
import json
from pathlib import Path
from ictai.semantic58 import run
from ictai.confirmation_six import confirm_six, CONTRACTS

ROOT=Path(__file__).resolve().parent
CASES=json.loads((ROOT/'dependency_variants.json').read_text())
CASES+=json.loads((ROOT/'baseline_cases.json').read_text())

def candidate_decision(observations):
    # A counterfactual only. No access to unavailable tools, hence cannot rule out
    # later competing diagnoses. Never use this to confirm production incidents.
    return confirm_six(observations,available_tools={x['tool']:1 for x in observations},exhausted=False)

def replay(case):
    # Reconstruct the controller's exact execution order using instrumented
    # tool_success events; results come from frozen fixture tool outputs.
    row=run(case,'B1_fixed',budget=12)
    names=[e['tool'] for e in row['audit'] if e['event']=='tool_success']
    evidence=[]; checkpoints=[]
    for name in names:
        evidence.append({'tool':name,'result':case['tools'][name]})
        strict=confirm_six(evidence,available_tools=case['tools'],exhausted=False)
        local=candidate_decision(evidence)
        checkpoints.append({'after_tool':name,'n':len(evidence),'strict':strict.status,
                            'strict_category':strict.category,'candidate':local.status,
                            'candidate_category':local.category})
    first=next((p for p in checkpoints if p['candidate']=='CONFIRMED'),None)
    return {'id':case['id'],'final_status':row['status'],'final_category':row['prediction'],
            'attempts':row['tool_calls'],'first_candidate_confirmation':first,
            'checkpoints':checkpoints}

def main():
    results=[replay(c) for c in CASES]
    # Counterexample: early schema mismatch, followed by independent pipeline failure.
    schema=next(c for c in CASES if 'schema_drift' in c['id'])
    original=schema['tools']
    first=[{'tool':t,'result':original[t]} for t in CONTRACTS['SCHEMA_DRIFT']]
    early=candidate_decision(first)
    combined=first+[
      {'tool':'inspect_task_execution','result':{'failed':True,'run_id':'affected-1'}},
      {'tool':'read_run_events','result':{'execution_error':True,'run_id':'affected-1'}}]
    final=confirm_six(combined,available_tools={x['tool']:1 for x in combined},exhausted=True)
    assert early.status=='CONFIRMED' and early.category=='SCHEMA_DRIFT',early
    assert final.status=='REVIEW_REQUIRED',final
    assert all(r['final_status'] in ('CONFIRMED','ABSTAINED','REVIEW_REQUIRED') for r in results)
    output={'cases':results,'adversarial_counterexample':{
      'early_category':early.category,'early_status':early.status,
      'after_competing_evidence_status':final.status,
      'after_competing_evidence_category':final.category,
      'warning':'Early category confirmation misses later competing positive evidence.'}}
    (ROOT/'stopping_study_results.json').write_text(json.dumps(output,indent=2))
    for r in results:
        p=r['first_candidate_confirmation']
        print(r['id'],'strict_final=',r['final_status'],r['final_category'],
              'attempts=',r['attempts'],'candidate_first=',p['n'] if p else 'none')
    print('ADVERSARIAL:',early.status,early.category,'->',final.status)
    print('STOPPING STUDY PASS — counterfactual only; no confirmation-policy changes')
if __name__=='__main__':main()
