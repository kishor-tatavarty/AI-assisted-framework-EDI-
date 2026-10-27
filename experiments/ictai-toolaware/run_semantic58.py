
"""Offline pilot by default; --live performs billable API requests."""
import argparse,csv,json
from pathlib import Path
from ictai.semantic_fixtures58 import build
from ictai.semantic58 import ARMS,run,evaluate,summarize
root=Path(__file__).resolve().parent
parser=argparse.ArgumentParser()
parser.add_argument("--live",action="store_true")
parser.add_argument("--limit",type=int,default=24)
args=parser.parse_args()
if not 1<=args.limit<=24:parser.error("limit must be 1..24")
cases,gold,history=build(root/"fixtures")
if args.live:
    try:
        from dotenv import load_dotenv
        load_dotenv(root/".env",override=True)
    except ImportError:pass
    from ictai.live_openai import OpenAIResponsesAdapter
    model=OpenAIResponsesAdapter()
else:
    def model(messages):
        data=json.loads(messages[-1]["content"]);s=data["symptoms"].lower()
        layer="validation" if any(x in s for x in ("customer_ref","field","blank","dashboard")) else "lineage" if "prerequisite" in s or "upstream" in s else "source" if any(x in s for x in ("supplier","partner","feed","extract","deadline")) else "pipeline"
        if layer not in data["available_layers"]:layer=data["available_layers"][0]
        return {"next_layer":layer,"hypotheses":[],"open_questions":[],"evidence_refs":[]}
rows=[]
for case in cases[:args.limit]:
    for arm in ARMS:
        result=run(case,arm,model=model if arm in ARMS[2:] else None,history=history if arm=="B4_knowledge" else ())
        result.update(evaluate(result,gold[case["id"]]))
        result["gold"]=gold[case["id"]];result["type"]=case["type"]
        rows.append(result)
folder=root/"results";folder.mkdir(exist_ok=True)
mode="live" if args.live else "mock"
fields=["id","type","arm","gold","prediction","status","correct","false_confirmation","correct_abstention","tool_calls","layers","llm_attempts","llm_failures","elapsed_ms"]
with (folder/f"phase58_{mode}_cases.csv").open("w",newline="") as f:
    writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
    writer.writerows({k:row[k] for k in fields} for row in rows)
(folder/f"phase58_{mode}_summary.json").write_text(json.dumps(summarize(rows),indent=2))
(folder/f"phase58_{mode}_audit.json").write_text(json.dumps(rows,indent=2))
if args.live:
    (folder/"phase58_live_model_records.json").write_text(json.dumps(model.records,indent=2))
    usage={"model":model.model,"successful_responses":len(model.records),
           "input_tokens":sum(x.get("usage",{}).get("input_tokens",0) for x in model.records),
           "output_tokens":sum(x.get("usage",{}).get("output_tokens",0) for x in model.records),
           "llm_elapsed_ms":round(sum(x.get("elapsed_ms",0) for x in model.records),3),
           "estimated_cost_usd":None,"cost_note":"Calculate using verified model pricing; not inferred."}
    (folder/"phase58_live_usage.json").write_text(json.dumps(usage,indent=2))
for item in summarize(rows):print(item)
print("SYNTHETIC DEVELOPMENT PILOT, not independent publication evidence. Live:",args.live)
