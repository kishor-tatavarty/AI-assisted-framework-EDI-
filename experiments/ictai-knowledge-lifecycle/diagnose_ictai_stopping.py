"""Read-only offline diagnostic for the ICTAI six-category conservative stop gate."""
import json
from pathlib import Path
from ictai.confirmation_six import confirm_six, CONTRACTS
from run_knowledge_routing_choice import SCENARIOS

ROOT=Path(__file__).resolve().parent
AUDIT=ROOT/'knowledge_routing_live_audit.json'
if not AUDIT.exists():
    AUDIT=ROOT/'results'/'knowledge_routing_live_audit.json'
if not AUDIT.exists():
    raise SystemExit('Copy knowledge_routing_live_audit.json into project root or results folder')
rows=json.loads(AUDIT.read_text(encoding='utf-8'))
fixtures={s['id']:s for s in SCENARIOS}
reports=[]
for row in rows:
    case=fixtures[row['id']]
    tools=case['tools']
    layers=[event['layer'] for event in row['audit'] if event.get('event')=='layer_selected']
    evidence=[]
    checkpoints=[]
    for layer in layers:
        from ictai.experiment57 import LAYERS
        for tool in LAYERS[layer]:
            if tool in tools and not any(e['tool']==tool for e in evidence):
                evidence.append({'tool':tool,'layer':layer,'result':tools[tool]})
        # Contrast strict policy with diagnostic 'observed-only' candidate.
        strict=confirm_six(evidence,available_tools=tools,exhausted=False)
        observed_only=confirm_six(evidence,available_tools={},exhausted=False)
        missing=sorted((set(tools)&set().union(*map(set,CONTRACTS.values())))-{e['tool'] for e in evidence})
        checkpoints.append({'layer':layer,'evidence_count':len(evidence),
            'strict_status':strict.status,'strict_category':strict.category,
            'observed_only_status':observed_only.status,
            'observed_only_category':observed_only.category,
            'unchecked_tools':missing})
    report={'id':row['id'],'arm':row['arm'],'layers':layers,'reported_tool_calls':row['tool_calls'],
            'replayed_evidence_count':len(evidence),'checkpoints':checkpoints,
            'reported_final_status':row['status'],'reported_final_category':row['prediction']}
    reports.append(report)
    print(json.dumps(report,indent=2))
output=ROOT/'results'/'stopping_diagnostic.json'
output.parent.mkdir(exist_ok=True)
output.write_text(json.dumps(reports,indent=2),encoding='utf-8')
print('Saved:',output)
print('READ-ONLY DIAGNOSTIC: observed-only is a counterfactual, NOT a safe replacement stopping policy.')
