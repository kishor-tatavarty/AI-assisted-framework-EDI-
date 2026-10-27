# ICTAI Phase 5.4 — Live model adapter

Includes the complete v5.3 baseline and a minimal OpenAI Responses API adapter using Python standard library. Offline tests mock the HTTP transport. **No real model call has been made unless `run_live54.py` is run with a valid API key.**

## Commands (PowerShell)
```powershell
python -m unittest discover -s tests -v
$env:OPENAI_API_KEY = 'YOUR_KEY_FROM_PLATFORM'  # set locally; never commit
$env:ICTAI_MODEL = 'gpt-4.1-mini'
python run_live54.py
Remove-Item Env:OPENAI_API_KEY
```

The live runner saves `results/phase54_live.json` containing model IDs, response IDs, usage, latency, raw proposals and investigation audit. This file may contain sensitive incident context in later experiments: review before sharing. Token cost is not estimated until pricing is verified and recorded. This is a smoke test, not a six-category benchmark. Do not add real customer data to this test.

**Known limitation:** The LLM currently sees the incident ID, visited layers, available layers and evidence but not the incident symptom text. This means the first-step proposal may not have enough information to choose an appropriate layer. Next step is to add a sanitized incident symptom field to the investigation context and compare with the deterministic baseline. The schema-drift fixture is not guaranteed to satisfy the current confirmation contract; inspect its actual output.
