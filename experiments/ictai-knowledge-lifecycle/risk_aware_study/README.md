# ICTAI Risk-Aware Stopping Study

Read-only counterfactual using the existing ICTAI confirmation contracts.
Does NOT modify production RCA or controller behavior.

Extract the `risk_aware_study` folder into `C:\research\ictai-knowledge-lifecycle`.
Run from the project root:

    python -m risk_aware_study.run_risk_aware_study

Expected: `RISK-AWARE STOPPING STUDY: PASS (read-only; no API calls)`.

Results are written to `risk_aware_study/risk_aware_results.json`.

Policy: after a candidate RCA is supported, require all tools belonging to
other potentially confirmable categories (those whose entire contracts exist
in the available tool inventory) before confirming. Do not infer negatives
from missing observations. In the supplied cases this saves zero calls,
because the pipeline-failure competing contract remains available.
A partial-inventory fixture demonstrates potential savings, but is not a
production guarantee. Adversarial schema + pipeline failure must request review.

This is a synthetic development study, not independent evidence of accuracy,
and cannot detect unmodeled causes, stale tool inventories, or unreliable
tool outputs. It does not execute GPT or make API calls.
