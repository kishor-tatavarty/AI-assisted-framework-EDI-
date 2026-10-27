# ICTAI Knowledge Lifecycle Patch

Includes a complete project snapshot based on the knowledge-reliability version. No `.env` included.

Changes: `PENDING` when declared current observations are missing; `ACCEPTED` only after declared checks pass; `REJECTED` for contradictions and provenance problems. Reassesses all retrieved candidates after evidence collection and records transitions. Only `ACCEPTED` records enter the LLM prompt.

**Design tradeoff:** Pending history cannot guide the initial LLM route in this conservative version. If future work uses pending hints to select diagnostic tools, it must do so through a separate untrusted-hint channel. Records with no declared checks may be accepted based on provenance alone, not factual corroboration. Contradiction checks cover only declared tool/key equality.

Install to a NEW folder, e.g. `C:\research\ictai-knowledge-lifecycle`; copy `.env` from your working folder only when live testing.

Run `python -m unittest discover -s tests -q` before any live call. No API calls needed for this patch verification.
