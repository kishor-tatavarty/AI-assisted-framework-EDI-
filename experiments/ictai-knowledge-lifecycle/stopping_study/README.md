# ICTAI category-specific stopping: read-only counterfactual

This experiment does **not** modify `confirmation_six.py`, the controller, or the dataset used in prior evaluations.

## Run
Extract the ZIP so the folder `stopping_study` is inside `C:\research\ictai-knowledge-lifecycle` (which should already include the 146-test tool-observability patch).

From the project root:

```powershell
python -m stopping_study.run_stopping_study
```

No API key or live model calls are needed. Results are saved to `stopping_study/stopping_study_results.json`.

## What is compared
The strict policy sees all available corroboration tools. The counterfactual category-only policy sees only observations collected so far, and therefore cannot detect an as-yet-unobserved competing diagnosis. It is **not a safe drop-in policy**.

On the frozen synthetic fixtures, category-only evidence is sufficient after two schema observations (versus four strict tool attempts). For confirmed dependency variants, both need four observations. Ambiguous dependency variants remain unresolved.

The adversarial test adds a genuine pipeline-failure signal after an early schema-drift signal. The category-only policy would have stopped with schema drift; the strict full-evidence decision instead returns `REVIEW_REQUIRED` because both categories have support. This illustrates the safety trade-off.

## Limitations
This is a diagnostic counterfactual on hand-authored synthetic cases. It does not prove safe tool savings. The next phase is to specify category-specific mandatory and competing-cause checks and test on independent scenarios before changing any stopping logic.
