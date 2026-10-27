# ICTAI Phase 5.5 — Six-category evidence contracts (incremental)

Based on the complete v5.4 package. Existing v5.4 controller, experiments and 62 tests are preserved.

**New modules:** `ictai/confirmation_six.py` and `ictai/reasoning_context.py`.

- `confirm_six(evidence, available_tools, exhausted)` implements conservative evidence checks for all six incident categories.
- `propose_with_symptoms(...)` passes observable incident symptoms, available layers, and current evidence to the LLM; never passes ground-truth labels.
- The existing live script `run_live54.py` still exercises the original two-category controller. This release does NOT wire the new six-category gate into the end-to-end controller; do not claim six-category end-to-end validation yet.
- Synthetic positive, incomplete, conflicting, and pending-evidence tests cover the new confirmation function.
- No live API call or new experiment was performed; no performance or publication-level accuracy claims.
- Evidence contracts are intentionally simplified. Timestamps use numeric epochs, not inferred text; data quality requires a measured count and matching rule ID. Pipeline and dependency symptoms can overlap; multiple supported categories trigger review rather than an arbitrary winner.
- A real experiment must distinguish root cause from downstream symptoms, test tool provenance and stale observations, and freeze independent ground truth.

Run `python -m unittest discover -s tests -v`.

**Next:** integrate the six-category gate and symptom-aware proposals into the bounded controller, add read-only tools for the new evidence types, then run paired six-category tests and live-model experiments.
