# ICTAI knowledge reliability development patch

Synthetic research prototype only. Adds provenance/date checks, explicit current-evidence contradiction checks and audit events. History is never used for final RCA confirmation. The fixture provenance fields are **synthetic**, not independently verified production records.

Extract to a NEW folder `C:\research\ictai-knowledge-reliability`. Copy `.env` locally if you intend to make live calls; it is excluded from this archive. Run `python -m unittest discover -s tests -q` first.

`python run_knowledge_use.py` is an offline retrieval preflight; `python run_knowledge_use.py --live` is billable (up to 64 calls). Do not run live until reviewing synthetic fixtures and validating the intended design.

**Limitations:** Checks cover explicitly declared tool/key equality only, not arbitrary natural-language contradictions or trustworthiness of reviewers. An `ACCEPTED` result means metadata and currently observed checks passed, not that the historical recommendation is true. Records with no current observations can remain pending; final RCA always uses deterministic current evidence. Knowledge-use causal benefit remains unproven.
