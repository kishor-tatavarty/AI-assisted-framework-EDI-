# ICTAI Phase 5.8 — Semantic investigation development package

This is a **synthetic development stress test**, not an independently validated dataset and not publication-grade performance evidence.

## Installation (Windows PowerShell)

Unzip into `C:\research\ictai-phase2`, preserving `.env` from your existing project. Never upload or commit `.env`.

```powershell
cd C:\research\ictai-phase2
python -m unittest discover -s tests -v
python run_semantic58.py
```

Expected: 88 tests pass; the offline runner generates `results/phase58_mock_cases.csv`, `results/phase58_mock_summary.json`, and `results/phase58_mock_audit.json`.

## Small live smoke test

Requires `OPENAI_API_KEY` and `ICTAI_MODEL` in `.env` and the existing OpenAI Responses API adapter. This **incurs API charges**. The limit applies to cases; two arms use the LLM, so 2 cases can generate multiple model calls.

```powershell
pip install python-dotenv
python run_semantic58.py --live --limit 2
```

Then review `results/phase58_live_cases.csv`, `results/phase58_live_summary.json`, `results/phase58_live_audit.json`, and `results/phase58_live_model_records.json`.

The `--live` mode sends synthetic incident text and retrieved runbook excerpts to the model. Do not substitute sensitive production records without a privacy review.

## Experimental arms

- B1: fixed-order evidence investigation
- B2: deterministic symptom routing
- B3: bounded LLM semantic layer proposals
- B4: bounded LLM proposals with retrieved verified training-only runbook snippets

The same `confirm_six` deterministic confirmation rules apply to every arm. LLM suggestions never count as RCA evidence. The controller uses no ground-truth label. Budgets: 12 evidence-tool calls, 4 LLM attempts, 5 distinct layers, at most 2 provisional confirmation rounds.

## Known limitations

1. The 24 development fixtures and 12 history records were authored from the known confirmation contracts; their high accuracy is circular and not evidence of generalization.
2. Training and test IDs are disjoint, but the training runbook text is semantically similar to the test prompts; stronger separation and independent authorship are required for confirmatory evaluation.
3. The offline mock is deliberately simplistic and **is not an LLM**. Its failed proposals are logged.
4. A real-model proposal can be accepted yet have no causal effect on the final decision. Compare per-case traces and layer order, not just LLM-call counts.
5. `confirm_six` conservatively checks all available corroboration; this can mask routing efficiency differences. Any revised stopping policy must be frozen and applied identically across arms before final testing.
6. The live adapter records model ID, response IDs, token usage, and latency. Monetary cost must be computed from verified prices at run time, not guessed.
7. No practitioner study, confidence intervals, independent 120-case held-out dataset, or full-scale live comparison is included.

## Next research step

Independently author/freeze a held-out incident corpus with misleading symptoms and decoy evidence, then run a small live pilot before a predeclared paired evaluation. Report negative findings and failure cases.
