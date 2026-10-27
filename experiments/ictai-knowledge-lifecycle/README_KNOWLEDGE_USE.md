# ICTAI B3/B4 Knowledge-use experiment

## What this does
Two frozen synthetic candidate incidents (schema-drift misleading and dependency-failure misleading) are compared across four historical-knowledge conditions:
- `relevant`: matching synthetic history record
- `irrelevant`: unrelated descriptions
- `stale`: relevant descriptions excluded by the stale flag
- `conflicting`: matching description, deliberately wrong suggested investigation layer

B3 never sees history; B4 sees filtered history. The runner uses the same current evidence and budget in each paired comparison. **These cases and records are development fixtures**, not independent evaluation data. The conflicting condition is a stress test, not an authenticated real-world conflict.

## On your computer
Extract to `C:\research\ictai-knowledge-use`. Copy `.env` from the working project locally, and never upload it.
```
Copy-Item "C:\research\ictai-knowledge-pilot\.env" "C:\research\ictai-knowledge-use\.env"
cd C:\research\ictai-knowledge-use
python -m unittest discover -s tests -q
python run_knowledge_use.py
```
The last command is OFFLINE and checks retrieval only. It should return 1/1/0/0 matches per case across relevant/conflicting/irrelevant/stale respectively.

## Live experiment
```
python run_knowledge_use.py --live
```
This is billable: 2 cases x 4 conditions x 2 arms, with up to 4 LLM calls per arm per case (up to 64 calls). B3 is intentionally repeated to assess run variability. Before running, verify that the two cases and 4 histories are appropriate.

Outputs: `results/knowledge_use_audit.json` and `results/knowledge_use_model_records.json`.

## Interpretation
Compare first layer, mean layers, evidence-tool calls, final classification, fallback, model time, accepted knowledge_refs and retrieved record IDs. Retrieval hits alone are not proof of knowledge usage; even accepted refs do not establish causality without a controlled comparison. A single stochastic run is a development diagnostic, not a performance estimate.

## Known limitations
The `conflicting` condition uses a misleading but flagged-verified synthetic record to stress-test defenses; the current retrieval component checks freshness and relevance, not factual correctness of the content. The knowledge-influenced-routing flag in the existing audit is a heuristic, not causal attribution. Dependency cases can abstain correctly if causal evidence is absent. Do not modify confirmation thresholds to improve labels.
