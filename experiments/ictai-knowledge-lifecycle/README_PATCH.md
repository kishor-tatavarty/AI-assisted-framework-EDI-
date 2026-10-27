# ICTAI tool observability patch

Overlay onto your **existing** `C:\research\ictai-knowledge-lifecycle` folder. Back up `ictai/semantic58.py` first. This ZIP contains only changed files and new tests. No .env.

Run `python -m unittest discover -s tests -q` after applying.

Adds `tool_attempt`, `tool_success`, `tool_error`, `confirmation_checkpoint`, `confirmation_final` audit events and `attempted_tool_calls`, `successful_observations`, `failed_tool_calls`, `supporting_evidence_refs` result fields. Existing `tool_calls` remains an alias for attempts for backward compatibility. Supporting references are not the same as all observations.

No stopping-policy or RCA confirmation changes. Tool failures are counted as attempts and do not generate evidence. Existing tool exception handling remains unchanged.

Caution: checkpoints use the controller's current confirmation status, not hypothetical observed-only confirmation. Results from previous runs cannot be retroactively reconstructed without rerunning.
