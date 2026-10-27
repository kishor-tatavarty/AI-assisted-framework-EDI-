import json,csv
from pathlib import Path
from ictai.experiment57 import run_case
root=Path(__file__).resolve().parent
cases=json.loads((root/'fixtures/pilot_inputs.json').read_text())
gold=json.loads((root/'fixtures/pilot_gold_DEV_ONLY.json').read_text())
def mock(messages):
 import json
 d=json.loads(messages[-1]['content']);s=d['symptoms'].lower()
 layer='validation' if any(w in s for w in ('schema','column','quality','invalid')) else 'pipeline' if any(w in s for w in ('dag','task','dependency','upstream')) else 'source'
 if layer not in d['available_layers']:layer=d['available_layers'][0]
 return {'next_layer':layer,'hypotheses':[],'open_questions':[],'evidence_refs':[]}
rows=[]
for case in cases:
 for arm in ('B1_fixed','B2_dynamic','B3_llm','B4_knowledge'):
  r=run_case(case,arm,model=mock if arm in ('B3_llm','B4_knowledge') else None)
  r['gold']=gold[case['id']];r['correct']=r['prediction']==r['gold'] and ((r['status']=='CONFIRMED')==(r['gold']!='INSUFFICIENT_EVIDENCE'))
  rows.append(r)
out=root/'results';out.mkdir(exist_ok=True)
with (out/'phase57_pilot_cases.csv').open('w',newline='') as f:
 fields=('id','arm','gold','prediction','status','correct','tool_calls','layers','llm_calls');w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows({k:r[k] for k in fields} for r in rows)
summary=[]
for arm in ('B1_fixed','B2_dynamic','B3_llm','B4_knowledge'):
 a=[r for r in rows if r['arm']==arm];summary.append({'arm':arm,'n':len(a),'accuracy':sum(r['correct'] for r in a)/len(a),'mean_tool_calls':sum(r['tool_calls'] for r in a)/len(a),'mean_layers':sum(r['layers'] for r in a)/len(a),'abstentions':sum(r['status']!='CONFIRMED' for r in a),'llm_calls':sum(r['llm_calls'] for r in a)})
(out/'phase57_pilot_summary.json').write_text(json.dumps(summary,indent=2))
(out/'phase57_pilot_audit.json').write_text(json.dumps(rows,indent=2))
for x in summary:print(x)
print('DEVELOPMENT ONLY: mock LLM, cold-start B4, hand-authored cases; not publication results.')
