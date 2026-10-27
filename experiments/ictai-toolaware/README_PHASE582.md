# Phase 5.8.2 — Knowledge reference normalization

Targeted change: when an LLM places an exact retrieved, verified, non-stale historical record ID in `evidence_refs`, the validator moves it to `knowledge_refs` and records `normalized_refs`. Unknown, stale, unverified or fabricated IDs still fail closed. Current-incident evidence remains the only evidence eligible for RCA confirmation.

This is a compatibility normalization, not proof that knowledge improved routing. The `knowledge_influenced_routing` audit flag is a heuristic and should not be interpreted as causal attribution without a controlled comparison.

Run `python -m unittest discover -s tests -v` and then `python run_semantic58.py --live --limit 2` (billable). Check `results/phase58_live_audit.json` for accepted B4 proposals, normalized_refs, and method=llm. Never upload `.env`.
