# ICTAI Phase 5.10 — Candidate Dataset and Independent Review Package

**Status: 120 candidate synthetic cases prepared, NOT independently adjudicated or frozen.** These were drafted programmatically with the existing controller evidence contracts, so they must not be represented as an independent test set or used for publication accuracy claims.

## Contents
- `phase510/candidate_inputs.json`: 120 case descriptions and tool observations (20 per intended incident category).
- `phase510/provisional_gold_NOT_FOR_CONFIRMATORY_USE.json`: development-only provisional labels, never to be shown to an investigator/model.
- `phase510/historical_candidate.json`: synthetic knowledge examples, not real historical incidents.
- `phase510/review_template.csv`: blank reviewer decisions; the provisional label is included only for adjudication, not for blinded first-pass labeling.
- `phase510/case_design_manifest.json`: drafting provenance.
- `phase510/dataset_manifest.json`: exact-hash and exact-overlap checks.

## Mandatory work before confirmatory evaluation
1. Independent domain expert(s) review the cases, verify operational plausibility, and author additional cases without consulting implementation rules. Reviewers must label from evidence before seeing provisional labels; create a blinded review sheet by removing `provisional_label`.
2. Fix ambiguous or inconsistent fixtures, and preserve an edit log. Avoid tailoring the test set to LLM or deterministic outcomes.
3. Replace synthetic history with training-only verified runbooks/incidents that are not near duplicates of held-out cases. Review semantic similarity manually.
4. Freeze a distinct held-out evaluation set, separate from any prompt/controller tuning. Store hashes, adjudicated gold and reviewer agreement.
5. Use `run_evaluation59.py` on approved inputs and gold only. Start with a small predeclared live pilot and budget estimate. Record all LLM response/usage traces and costs.

## Caution
- 120 generated candidate cases are *not* 120 independent empirical incidents.
- The existing conservative confirmation gate may require every available tool and can erase routing advantages; report this limitation.
- Category names and provisional labels are excluded from model input but still present in review/manifest files. Never load review/manifest files into model prompts.
- This package is for curation and integrity checks, not a claim of measured AI benefit.

## Regression test
`python -m unittest discover -s tests -v`
