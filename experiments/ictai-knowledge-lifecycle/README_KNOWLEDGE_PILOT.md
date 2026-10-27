# ICTAI B4 Knowledge Retrieval — Development Pilot

Overlay/working copy built from the tool-aware project plus eligibility-consistency patch.
All 134 local tests passed. The changes are confined to advisory retrieval in
`ictai/semantic58.py`, a synthetic history fixture, and five regression tests.

## Behavior
- Retrieves only `verified=True`, `stale=False` records, and only for eligible layers.
- Uses at least two distinctive overlapping terms and otherwise abstains.
- Keeps deterministic confirmation unchanged; retrieved history is never current evidence.
- Logs `knowledge_retrieval_status` (MATCHED/ABSTAINED).
- B3 is unchanged; B4 alone gets retrieved context.

## Important scientific limitation
The two sample records in `evaluation12/historical_semantic_pilot.json`
are **synthetic test fixtures**, not independently verified historical incidents.
Their `verified=True` flag means they are accepted by the prototype's simulated
record-validation contract, NOT that they were verified by practitioners.
Do not use these as real-world historical evidence.

This lexical pilot is not semantic embedding retrieval. Matching exact words
across paraphrases is limited; assess retrieval quality and distractor behavior
before investing in embeddings.

## Install
Extract into a NEW directory, e.g. `C:\research\ictai-knowledge-pilot`.
Copy your existing `.env` there locally (never share it).
Run `python -m unittest discover -s tests -q`.

## Safe first check (no API calls)
```
python -c "from ictai.semantic58 import retrieve; import json; h=json.load(open('evaluation12/historical_semantic_pilot.json')); print(retrieve(h,'Partner deployment triggered parser rejects after unexpected attributes',{'validation','lineage'}))"
```

## Experimental design
Do not run a full 12-case LLM evaluation with these two examples and claim a
knowledge benefit: the cases were not independently selected to match them.
First assemble 2+ realistic, independently reviewed historical cases with
provenance, time-validity, and access controls; freeze a separate held-out
evaluation set with relevant, irrelevant, stale and conflicting retrieval cases.
Compare B3 vs B4 with the same model, current evidence and budget, and audit
accepted knowledge_refs, routing changes, confirmation and cost.
