# Phase 5.8.1 — Knowledge-reference separation

- `evidence_refs`: only current incident tool evidence. Fabricated references are rejected.
- `knowledge_refs`: only retrieved, verified, non-stale historical record IDs. Never sufficient to confirm RCA.
- Historical records are passed as a structured `retrieved_knowledge` input, not appended to incident symptoms.
- Invalid historical references are rejected; deterministic fallback remains active.
- Backward compatibility: proposals without `knowledge_refs` remain valid.
- Audit logs distinguish accepted proposals, knowledge citations, and whether a knowledge-citing proposal changed routing relative to deterministic routing. This last indicator is *not causal proof* of knowledge's contribution.
- The live model must actually emit `knowledge_refs`; no guarantee it will. Do not relax `evidence_refs` validation to make a live test pass.
- Do not include `.env` in any archive or commit. Run `python -m unittest discover -s tests -v`, then `python run_semantic58.py --live --limit 2` for billable validation.
- Synthetic development cases are not publication evidence.
