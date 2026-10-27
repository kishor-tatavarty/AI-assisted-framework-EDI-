
"""Read-only evidence scheduling replay. No API calls, no controller mutations."""
import argparse,json
from pathlib import Path
from ictai.semantic58 import run
from ictai.confirmation_six import confirm_six, CONTRACTS
from ictai.experiment57 import LAYERS

ROOT=Path(__file__).resolve().parent

def tool_order(case, layer_order):
    seen=[]
    for layer in layer_order:
        for tool in LAYERS.get(layer,()):
            if tool in case['tools'] and tool not in seen: seen.append(tool)
    seen.extend(t for t in case['tools'] if t not in seen)
    return seen

def replay(case, order):
    available=case['tools']; evidence=[]; first_candidate=None; first_strict=None; first_causal=None
    events=[]
    for n,tool in enumerate(order,1):
        evidence.append({'tool':tool,'result':available[tool]})
        # Provisional or confirmed is a supported single-cause candidate under full inventory.
        strict=confirm_six(evidence,available_tools=available,exhausted=False)
        observed=confirm_six(evidence,available_tools={t:available[t] for t in order[:n]},exhausted=False)
        if first_candidate is None and strict.status in ('PROVISIONAL_RCA','CONFIRMED'):
            first_candidate=n
        if first_strict is None and strict.status=='CONFIRMED':first_strict=n
        if first_causal is None and observed.category=='DEPENDENCY_FAILURE' and observed.status in ('CONFIRMED','PROVISIONAL_RCA'):
            first_causal=n
        events.append({'call':n,'tool':tool,'strict_status':strict.status,'strict_category':strict.category})
    final=confirm_six(evidence,available_tools=available,exhausted=True)
    return {'order':order,'first_supported_candidate_call':first_candidate,
            'first_dependency_causal_evidence_call':first_causal,
            'first_strict_confirmation_call':first_strict,'total_calls':len(order),
            'final_status':final.status,'final_category':final.category,'checkpoints':events}

def extract_layers(row):
    return [e['layer'] for e in row.get('audit',[]) if e.get('event')=='layer_selected']

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--live-audit',help='Optional existing B3/B4 audit JSON (read-only); does not call API')
    ap.add_argument('--output',default='results/evidence_scheduling_phase1.json')
    a=ap.parse_args()
    cases=json.loads((ROOT/'evaluation12/inputs_12.json').read_text())
    # Also include confirmed dependency fixtures, separately identified as synthetic variants.
    extra=json.loads((ROOT/'dependency_fixture_checks/dependency_variants.json').read_text())
    cases=cases+extra
    live={}
    if a.live_audit:
        for row in json.loads(Path(a.live_audit).read_text()):
            if row.get('arm') in ('B3_llm','B4_knowledge'):
                live[(row['id'],row['arm'])]=row
    rows=[]
    for case in cases:
        b2=run(case,'B2_dynamic',budget=12)
        baseline_layers=extract_layers(b2)
        # B2 observed order from its actual tool_attempt audit, including provisional corroboration.
        b2_order=[e['tool'] for e in b2['audit'] if e.get('event')=='tool_attempt']
        baseline=replay(case,b2_order)
        rows.append({'id':case['id'],'arm':'B2_dynamic','source':'executed_offline','layers':baseline_layers,**baseline})
        for arm in ('B3_llm','B4_knowledge'):
            row=live.get((case['id'],arm))
            if row is None:continue  # never fabricate LLM decisions
            layers=extract_layers(row)
            order=[e['tool'] for e in row['audit'] if e.get('event')=='tool_attempt']
            source='recorded_live_tool_attempts'
            if not order:
                order=tool_order(case,layers)
                source='reconstructed_from_recorded_live_layers'
            # Keep only case tools, dedupe; append residual corroboration in original fixture order.
            order=list(dict.fromkeys(t for t in order if t in case['tools']))
            order.extend(t for t in case['tools'] if t not in order)
            result=replay(case,order)
            rows.append({'id':case['id'],'arm':arm,'source':source,'layers':layers,**result})
    out=ROOT/a.output;out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(rows,indent=2))
    from collections import Counter
    print('Rows:',len(rows),'Arms:',dict(Counter(r['arm'] for r in rows)))
    for r in rows:
        if 'schema_drift' in r['id'] or 'dependency_failure' in r['id']:
            print(r['id'],r['arm'],'first_candidate',r['first_supported_candidate_call'],
                  'causal',r['first_dependency_causal_evidence_call'],
                  'strict',r['first_strict_confirmation_call'],'final',r['final_status'])
    print('Saved:',out)
    print('READ-ONLY REPLAY. No model calls; LLM arms only if a prior live audit is supplied.')
if __name__=='__main__':main()
