# ICTAI Phase 5.6 — Six-category integration

Run: `python -m unittest discover -s tests -v`

New: `ictai/experiment55.py`, `tests/test_experiment55.py`.

`investigate_six(incident_id, symptoms, tools, model_callable=None, max_tool_calls=12, max_llm_calls=4, max_layers=5, max_rounds=2)` accepts read-only callable tool adapters. It never receives ground-truth RCA labels. LLM proposals are validated; invalid responses fall back to deterministic symptom-based routing. `confirm_six` determines RCA independently from evidence.

Limits: This is a controlled fixture integration, not a held-out benchmark. Deterministic routing uses simple symptom keyword heuristics. Knowledge-assisted routing is not yet integrated here. The confirmation gate treats all tool outputs as trusted test fixtures, and its conservative requirement to inspect other available tools can increase work. Confirmation can still miss contradictions from unavailable or unqueried tools. Tool outputs and timestamp schemas need production adapters. The model is mocked in these tests; live six-category API execution has not occurred. Avoid claims of accuracy, confidence calibration, latency savings, or LLM benefit from these tests.

Next: freeze independent cases and ground truth, build identical-evidence paired baseline runner, record model responses, latency, token usage, and per-case failure reasons. Add a controlled knowledge-assisted arm only after implementing actual knowledge-driven routing.
