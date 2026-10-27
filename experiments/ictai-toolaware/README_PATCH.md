# ICTAI Eligibility Consistency Patch

Apply to **ICTAI Tool-Aware Routing Improvement** project only. This is a small overlay, not a new research implementation.

## Change
- Shared `eligible_tools_by_layer` in `ictai/llm_reasoner.py` combines original tools and six-category extra tools, excludes visited layers and observed tools.
- Prompt builder and validator now consult exactly the same function.
- Semantic runner uses the same map to select eligible layers.
- RCA confirmation contracts, budgets, knowledge retrieval, and datasets are unchanged.

## Install (PowerShell)
Extract the patch ZIP to `C:\research\ictai-toolaware` and allow the three `ictai/*.py` files to overwrite their counterparts. Keep your `.env` in place. Do not overwrite the project with an older archive.

## Validate
`python -m unittest discover -s tests -v`

Then test on a small live subset before the 12-case rerun. A successful patch should eliminate false `no_available_tools` rejections for available `inspect_quality_rule` and `inspect_freshness_sla` tools. Rejection of genuinely exhausted or unavailable tools must remain intact.

## Evaluation caution
The patch is developed using known failing development cases. Use a separate held-out set for performance claims. No changes to confirmation rules or provisional labels.
