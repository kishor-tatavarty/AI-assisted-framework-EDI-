# ICTAI Phase 5 — Synthetic Pilot Evaluation

Run `python -m unittest discover -s tests -v` and `python run_experiment.py`.

Three paired arms: fixed-order B1, signal-based dynamic B2, and knowledge-assisted B3. B3 uses verified, non-evaluation runbooks to prioritize the first evidence layer. All arms share the same fixture evidence and tool-call budget. RCA is the same deterministic classifier in all arms.

**Limitations:** 10 hand-authored synthetic cases only (missing file, schema drift, abstention). Signal hints sometimes coincide with truth, sometimes do not. There is no LLM, independent field dataset, human study, production timing, or calibrated confidence. Knowledge advice does not override current evidence. The current controller collects evidence until exhaustion, not until RCA sufficiency, so no speed advantage is guaranteed. Latency here is Python execution overhead, not end-to-end operational latency. Do not present these results as generalizable or publication-ready.

`results/pilot_cases.csv` contains case-level decisions, audit-relevant tool counts and evidence refs. `results/pilot_summary.json` contains descriptive aggregates. No statistical significance claim is justified.

Next: refine stopping rule, blind larger independent fixtures, expand to six incident categories, add leakage-safe knowledge ablation, assess paired differences and collect human review.
