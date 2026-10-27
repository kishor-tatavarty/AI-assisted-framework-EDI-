ICTAI confirmation-policy and tool-accounting audit (read only)

Copy ictai_confirmation_accounting_audit.py into your existing
C:\research\ictai-knowledge-lifecycle directory.
Run: python ictai_confirmation_accounting_audit.py

No .env required. No billable calls. No source files modified.

Findings from code inspection:
1) confirmation_six.py's global corroboration gate waits for all available
   tools participating in any of the six category contracts, even after a
   category's primary evidence has established a provisional RCA.
2) semantic58.py counts len(used) as tool_calls; it adds a tool to used before
   executing it, so failures are counted as attempts but not as observations.
3) PROVISIONAL_RCA triggers remaining-tool execution without recording new
   layer_selected events. Therefore layer-based evidence reconstruction can
   undercount evidence actually collected. Final evidence_refs intentionally
   list only supporting evidence, not all observations.

The script prints available tools and primary/global corroboration sets for
existing cases. It does not change stopping policy or claim tool-call savings.

Recommended next code change (not included): audit every tool_attempt,
tool_success and tool_error, record evidence counts, and log confirmation
checkpoints. Only then evaluate category-specific corroboration policies
against conflict-injection regression tests.
