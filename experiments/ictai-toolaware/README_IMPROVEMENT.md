# ICTAI targeted tool-aware routing improvement

Development branch; original benchmark remains frozen.

Changes: model prompt now lists only unvisited layers with unconsumed eligible tools, including six-category extension tools. Runner uses the same eligibility definition. No RCA confirmation rule is weakened.

Dependency cases `-05` and `-13` are missing the `blocked_by_upstream` signal and include an unrelated run; **do not relabel as confirmed** without independent evidence.

Run `python -m unittest discover -s tests -v`. To evaluate offline first, run `python run_evaluation59.py --inputs evaluation12/inputs_12.json --gold evaluation12/provisional_gold_12.json --history evaluation12/historical_train_candidate.json --budget 12 --output results/toolaware_offline`.

Then test a *single* live case first using a separately prepared one-case JSON input/gold pair before spending on the full live run. Copy `.env` locally only; never share it. This is a development change, not a confirmatory experiment.
