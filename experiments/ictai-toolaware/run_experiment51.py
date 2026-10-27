import csv, json
from pathlib import Path
from ictai.experiment51 import run_experiment, summarize, error_analysis
out=Path('results'); out.mkdir(exist_ok=True)
rows=run_experiment(); summary=summarize(rows); errors=error_analysis(rows)
for name,records in [('phase51_cases.csv',rows),('phase51_error_analysis.csv',errors)]:
    with (out/name).open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=records[0].keys()); writer.writeheader();writer.writerows(records)
(out/'phase51_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
for record in summary: print(record)
print('Saved case-level results, error analysis, and summary under results/')
