"""Knowledge-use experiment: paired B3/B4, same cases, four history conditions."""
import argparse, json, hashlib
from pathlib import Path
from ictai.semantic58 import run, evaluate, retrieve
from ictai.evaluation59 import validate_dataset
p=argparse.ArgumentParser()
p.add_argument("--live",action="store_true")
p.add_argument("--output",default="results/knowledge_use")
args=p.parse_args()
root=Path(__file__).resolve().parent
cases=json.loads((root/"evaluation12/knowledge_use_inputs.json").read_text())
gold=json.loads((root/"evaluation12/knowledge_use_provisional_gold.json").read_text())
model=None
if args.live:
    from dotenv import load_dotenv
    load_dotenv(root/".env",override=True)
    from ictai.live_openai import OpenAIResponsesAdapter
    model=OpenAIResponsesAdapter()
rows=[]
for condition in ("relevant","irrelevant","stale","conflicting"):
    history=json.loads((root/f"evaluation12/history_{condition}.json").read_text())
    validate_dataset(cases,gold,history)
    for case in cases:
        # Live B3 and B4 both use the same incident and model.
        if not args.live:
            # Offline retrieval preflight, no claims about LLM routing.
            hits=retrieve(history,case["symptoms"],eligible_layers={"source","validation","pipeline","lineage"})
            rows.append({"condition":condition,"id":case["id"],"arm":"B4_knowledge","retrieval_preflight":hits})
            continue
        for arm in ("B3_llm","B4_knowledge"):
            r=run(case,arm,model=model,history=history,budget=12)
            r.update(evaluate(r,gold[case["id"]]))
            r["condition"]=condition
            r["retrieval_count"]=len(r["knowledge_hits"])
            r["knowledge_refs_accepted"]=sorted(set(ref for ev in r["audit"] if ev.get("event")=="llm_proposal" and ev.get("accepted") for ref in ev.get("knowledge_refs",[])))
            rows.append(r)
out=root/args.output;out.parent.mkdir(parents=True,exist_ok=True)
(out.with_name(out.name+"_audit.json")).write_text(json.dumps(rows,indent=2))
if model is not None:
 (out.with_name(out.name+"_model_records.json")).write_text(json.dumps(model.records,indent=2))
for r in rows:
 print(r["condition"],r["id"],r["arm"],
       "retrieved",r.get("retrieval_count",len(r.get("retrieval_preflight",[]))),
       "accepted_refs",r.get("knowledge_refs_accepted",[]),
       "layers",r.get("layers","-"),"correct",r.get("correct","-"),
       "llm_failures",r.get("llm_failures","-"))
print("Done. Synthetic development comparison; no independent validity claim.")
