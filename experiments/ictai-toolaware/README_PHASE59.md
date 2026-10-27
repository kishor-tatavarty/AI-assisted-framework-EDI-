# ICTAI Phase 5.9 — Independent evaluation protocol

This release **does not claim to provide an independent held-out dataset**. It supplies a protocol and runner for externally curated cases. The included Phase 5.8 fixtures are development-only and must not be used as confirmatory evidence.

## Required JSON inputs
- `--inputs`: list of `{"id", "symptoms", "tools", "type"}`. No ground-truth label in these records.
- `--gold`: mapping of case IDs to gold root cause (or `INSUFFICIENT_EVIDENCE`).
- `--history`: verified, non-stale historical records with IDs distinct from test IDs.

## Procedure
1. Have an independent author or domain expert construct and adjudicate 120 cases (20 per category) without reference to controller rules or prompts.
2. Ensure each case has an evidence-source inventory and independently established gold label.
3. Curate training-only historical records with no near-duplicate held-out descriptions.
4. Freeze the three input files and record their SHA-256 hashes.
5. Pilot on a separate development subset; do not tune prompts after confirmatory results are inspected.
6. Run fixed and dynamic baselines, then live LLM arms on exactly the same cases, budget, tool outputs and confirmation gates.
7. Review all incorrect confirmations, abstentions and tool errors. Record repeated live LLM trials and API costs separately.

## Commands
```
python -m unittest discover -s tests -v
python run_evaluation59.py --inputs YOUR_INPUTS.json --gold YOUR_GOLD.json --history YOUR_HISTORY.json --budget 3
python run_evaluation59.py --inputs YOUR_INPUTS.json --gold YOUR_GOLD.json --history YOUR_HISTORY.json --budget 3 --live
```

`--live` incurs API costs and loads `.env` if python-dotenv is installed.

## Important caveats
- The existing confirmation gate deliberately checks *all available tools* before final confirmation; a tight budget may force abstention even when the root cause is already supported. This must be reported, not disguised as a routing effect.
- Tool call counting measures attempts in the current runner; source-tool costs are not production-calibrated.
- The current B4 uses simple lexical retrieval, not embedding-based semantic retrieval.
- Retrieved historical records are not evidence for current RCA.
- No practitioner assessment, calibrated uncertainty, or independent evaluation has been performed by this release.
- A near-duplicate semantic leakage review is still required; the manifest only detects exact text duplication and ID overlap.
