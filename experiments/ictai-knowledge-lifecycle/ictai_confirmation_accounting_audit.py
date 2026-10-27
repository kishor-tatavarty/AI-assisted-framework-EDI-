"""Read-only ICTAI confirmation/tool accounting audit; no API calls."""
import json, sys
from pathlib import Path
root=Path(__file__).resolve().parent
sys.path.insert(0,str(root))
from ictai.semantic58 import run
from ictai.confirmation_six import confirm_six, CONTRACTS
cases=json.loads((root/'evaluation12/knowledge_use_inputs.json').read_text())
if not cases:
    cases=json.loads((root/'evaluation12/inputs_12.json').read_text())
for case in cases:
    row=run(case,'B1_fixed',budget=12)
    available=set(case['tools']); all_contract_tools=set().union(*(set(x) for x in CONTRACTS.values()))
    primary=set(CONTRACTS.get(row['prediction'],()))
    print(json.dumps({'id':case['id'],'prediction':row['prediction'],'status':row['status'],
        'attempted_tool_calls':row['tool_calls'],'evidence_refs_in_final_decision':row['evidence_refs'],
        'layers_selected':row['layers'],'available_tool_names':sorted(available),
        'primary_contract_tools':sorted(primary),'global_corrob_tools':sorted(available & all_contract_tools),
        'note':'Final evidence_refs are supporting references only, not a complete record of executed tools.'},indent=2))
print('READ-ONLY AUDIT COMPLETE. No API calls; no confirmation changes.')
