"""Generate reproducible pilot output (runtime measurements vary)."""
import csv, json
from pathlib import Path
from ictai.experiment import run_pilot, summarize
out=Path('results');out.mkdir(exist_ok=True)
rows=run_pilot()
with (out/'pilot_cases.csv').open('w',newline='',encoding='utf-8') as f:
    writer=csv.DictWriter(f,fieldnames=rows[0].keys());writer.writeheader();writer.writerows(rows)
summary=summarize(rows)
(out/'pilot_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
for item in summary: print(item)
print('Saved results/pilot_cases.csv and results/pilot_summary.json')
