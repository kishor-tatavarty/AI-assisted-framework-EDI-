# ICTAI 12-case live comparison (development experiment)

This is a frozen *synthetic candidate* subset: one semantic and one misleading case from each of six categories. The cases were authored from the prototype's evidence contracts and are **not independently adjudicated**.

## Already executed offline
`results/phase12_offline_summary.json` and `results/phase12_offline_audit.json` contain B1/B2 outcomes with 12-tool budget. B1 and B2 each had 10/12 provisional-label matches; these are development outcomes, not publication accuracy.

## On your computer (PowerShell)
Extract to a separate folder, e.g. `C:\research\ictai-live12`. Keep your real `.env` file **outside the ZIP** and copy it into the extracted project root locally. Never upload it.

```
cd C:\research\ictai-live12
python -m unittest discover -s tests -v
python run_evaluation59.py --inputs evaluation12/inputs_12.json --gold evaluation12/provisional_gold_12.json --history evaluation12/historical_train_candidate.json --budget 12 --live --output results/phase12_live
```

The live command reruns B1/B2 as well as B3/B4, with identical case IDs, evidence fixtures and budget. It makes billable LLM requests. Depending on routing, the cap is 4 model calls per LLM arm per case (up to 96 model calls for 12 cases).

## Outputs
- `results/phase12_live_summary.json`: four-arm summary
- `results/phase12_live_audit.json`: paired case-level traces
- `results/phase12_live_model_records.json`: model IDs, raw responses, usage and latency
- `results/phase12_live_manifest.json`: case/label/history hashes

Inspect and redact logs before sharing; raw prompts or outputs may contain incident details.

## Limitations
- Provisional gold labels are used for development scoring only.
- The knowledge repository contains six synthetic training candidates; there is no independently verified knowledge corpus.
- Existing B1/B2 and B3/B4 arms share confirmation logic but model latency is not comparable to local in-memory tool latency.
- An independent case review and a separate blinded practitioner assessment are required before manuscript-level claims.
