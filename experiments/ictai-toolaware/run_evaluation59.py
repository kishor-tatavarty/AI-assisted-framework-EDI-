
"""Read separately curated inputs/gold/history. Never send gold to a model."""
import argparse,json,csv
from pathlib import Path
from ictai.evaluation59 import validate_dataset,run_paired,summary
p=argparse.ArgumentParser()
p.add_argument("--inputs",required=True)
p.add_argument("--gold",required=True)
p.add_argument("--history",required=True)
p.add_argument("--budget",type=int,default=3)
p.add_argument("--live",action="store_true")
p.add_argument("--output",default="results/phase59")
args=p.parse_args()
inputs=json.loads(Path(args.inputs).read_text())
gold=json.loads(Path(args.gold).read_text())
history=json.loads(Path(args.history).read_text())
manifest=validate_dataset(inputs,gold,history)
print("Dataset manifest:",json.dumps(manifest,indent=2))
if manifest["duplicate_history_descriptions"]:
    raise SystemExit("Exact historical description leakage; revise dataset.")
model=None
if args.live:
    try:
        from dotenv import load_dotenv
        load_dotenv(Path(__file__).resolve().parent/".env",override=True)
    except ImportError:pass
    from ictai.live_openai import OpenAIResponsesAdapter
    model=OpenAIResponsesAdapter()
rows=run_paired(inputs,gold,history,model=model,budget=args.budget)
out=Path(args.output);out.parent.mkdir(parents=True,exist_ok=True)
out.with_name(out.name+"_manifest.json").write_text(json.dumps(manifest,indent=2))
out.with_name(out.name+"_summary.json").write_text(json.dumps(summary(rows),indent=2))
out.with_name(out.name+"_audit.json").write_text(json.dumps(rows,indent=2))
if model is not None:
    out.with_name(out.name+"_model_records.json").write_text(json.dumps(model.records,indent=2))
for s in summary(rows):print(s)
print("Evaluation runner complete. Scientific independence requires external dataset review.")
