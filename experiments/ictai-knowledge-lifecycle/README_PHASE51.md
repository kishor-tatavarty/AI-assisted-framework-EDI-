# ICTAI Phase 5.1: Evidence-sufficiency stopping and error analysis

This **adds** `ictai/experiment51.py` without changing the v5 controllers, classifier, repository, or pilot results. The three arms use the same tool fixtures, call budget, and per-tool stopping criterion. Classification is checked after each successful or failed tool call, and execution stops on `CLASSIFIED` (never on abstention).

Run `python -m unittest discover -s tests -v` and `python run_experiment51.py`.

Outputs: `results/phase51_cases.csv`, `results/phase51_error_analysis.csv`, `results/phase51_summary.json`.

**Scientific caveats:** The early-stop policy can be premature when later evidence would contradict a preliminary supported cause (especially AB04). This version measures that limitation, not a safe production stop. It also cannot detect unseen contradictory evidence. A validation/confirmation gate is needed before treating early stops as reliable RCA. The case labels include `INSUFFICIENT_EVIDENCE` as an expected outcome, so headline accuracy conflates RCA correctness and appropriate abstention; report separately. These are ten designed synthetic cases, not independent operational evidence. Sub-millisecond Python latency is not realistic tool or LLM latency. The knowledge arm uses a simple signal-to-runbook priority, not semantic RAG.
