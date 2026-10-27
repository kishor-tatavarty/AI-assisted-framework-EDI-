# Phase 5.7: paired offline development pilot

Run `python -m unittest discover -s tests -v` and `python run_experiment57.py`.

12 hand-authored synthetic cases: 2 per category (supported and incomplete). Gold labels in a separate DEV_ONLY file are joined only after controller predictions. B1 fixed, B2 symptom dynamic, B3 mocked LLM, B4 mocked LLM plus optional knowledge routing. The B4 pilot deliberately has no vetted historical records: it is a cold-start arm, NOT evidence of knowledge benefit. `test_knowledge_changes_route` proves the code path can change selection, not that retrieval is scientifically useful.

No live model requests or API charges. No model latency/cost claims. These cases are coupled to the six-category rules, so they are unsuitable as confirmatory evidence. For a publishable study: build independently adjudicated held-out cases; training-only verified knowledge; enforce leakage checks; evaluate real LLM proposals and knowledge retrieval; analyze errors and run paired uncertainty estimates. Do not present this pilot as a four-arm performance benchmark.
