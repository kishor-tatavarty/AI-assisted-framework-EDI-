# ICTAI dependency evidence fixture supplement

This package ADDS four synthetic development fixtures without changing original 12-case inputs, labels, or RCA confirmation logic.

Two original evidence patterns are retained as `__ambiguous` variants: upstream unhealthy + lineage relation but no affected-run causal event. Expected outcome: abstain.

Two `__confirmed` variants add an explicitly blocked affected-run event, a matching upstream identifier, and an affected execution ID. Expected outcome: DEPENDENCY_FAILURE confirmed.

`execution_error` is left false in the confirmed variants to avoid implying that an upstream-blocked run must also have a local execution error. The existing contract checks `blocked_by_upstream`.

## Installation
Extract files into `C:\research\ictai-knowledge-lifecycle\dependency_fixture_checks` (one folder).
Run from project root:
`python dependency_fixture_checks/run_dependency_fixture_checks.py`

No .env and no API requests needed. Tests rely on the existing project's `ictai` package. If imports fail, run with `python -m dependency_fixture_checks.run_dependency_fixture_checks` from project root.

These are engineered synthetic fixtures with provisional expected outcomes, not independent adjudication or production evidence. They cannot retroactively change prior experiment accuracy.
