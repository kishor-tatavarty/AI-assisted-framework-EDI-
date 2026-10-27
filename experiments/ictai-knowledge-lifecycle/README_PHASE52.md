# ICTAI Phase 5.2 — Conservative RCA Confirmation Gate

Adds `ictai/confirmation.py`, `ictai/experiment52.py`, and eight tests. Keeps prior v5.1 files and tests unchanged.

Run `python -m unittest discover -s tests -v`.

The two existing RCA classes (missing file and schema drift) are subject to an additional confirmation pass over available RCA-relevant tools, to catch conflicting causes that early stopping could miss. Budget exhaustion while confirmation checks remain results in `REVIEW_REQUIRED`, not false confirmation. Missing evidence results in abstention. The gate records provenance via evidence indices, not stable external event IDs.

**Limits:** The other four incident categories are NOT implemented. The current tool adapters are synthetic; a tool returning a false or stale observation can still mislead the gate. Confirmation covers only available registered tools, not all possible external evidence. This is an engineering safety improvement, not a measured increase in RCA accuracy. `run_experiment51.py` is intentionally unchanged for historical comparability. Do not describe this package as a six-category or LLM evaluation.
