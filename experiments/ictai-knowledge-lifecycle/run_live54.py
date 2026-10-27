"""Run two synthetic live cases; requires OPENAI_API_KEY. No live claims without actual API call."""
import json
from pathlib import Path
from ictai.live_openai import OpenAIResponsesAdapter
from ictai.experiment53 import investigate_llm

def cases():
    return [
      ('missing-01','missing_file',{'inspect_manifest':lambda:{'expected':True},'check_object_inventory':lambda:{'present':False}}),
      ('schema-01','schema_drift',{'inspect_schema_contract':lambda:{'columns':['id','amount']},'inspect_observed_schema':lambda:{'columns':['id','amount','unexpected']}}),
    ]

def main():
    model=OpenAIResponsesAdapter()
    output=[]
    for name,signal,tools in cases():
        start=len(model.records)
        ctx,decision=investigate_llm(name,signal,tools,model,max_llm_calls=4)
        output.append({'incident_id':name,'status':decision.status,'category':decision.category,
                       'visited':ctx.visited,'audit':ctx.audit,'llm_records':model.records[start:]})
    target=Path('results/phase54_live.json');target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps(output,indent=2))
    for row in output: print(row['incident_id'],row['status'],row['category'],'LLM calls:',len(row['llm_records']))
    print('Saved:',target)

if __name__=='__main__': main()
