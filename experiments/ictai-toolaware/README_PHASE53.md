# Phase 5.3: Bounded LLM proposal adapter

This increment introduces **one untrusted LLM reasoning component**. It does not require an API key for offline tests and does **not** claim a live LLM was evaluated.

- `ictai/llm_reasoner.py`: structured JSON proposal contract, evidence-reference checks, model callable adapter.
- `ictai/experiment53.py`: bounded LLM calls (default 4), tool calls (12), layers (5), confirmation rounds (2); deterministic routing fallback on invalid proposals or model errors; existing confirmation gate remains authoritative.
- `tests/test_llm_reasoner.py`: adversarial proposals, fallback, budgets, and end-to-end fixture.

Run: `python -m unittest discover -s tests -v`

## Optional real-model integration

Provide a callable `model_callable(messages)` that invokes a configured LLM and returns a JSON object or JSON string. Never place API keys in source files. Record the actual provider, model identifier/version, sampling parameters, prompt, token counts, costs, latency, and raw/validated proposals in a controlled experiment. Do not send confidential logs or PII to a third-party model without authorization. Real-model integration has **not** been executed in this package.

## Limitations

- Phase 5.2 confirmation currently supports only missing-file and schema-drift RCA. Other categories remain future work.
- A syntactically valid LLM proposal may be strategically wrong; comparison with deterministic routing is required.
- LLM hypotheses and questions are proposals only, not facts; the deterministic classifier never reads them.
- Tool availability and trustworthiness are assumptions of the test fixtures. Production adapters need evidence authenticity and timestamp checks.
- The pilot experiment is not a publication-grade benchmark.
