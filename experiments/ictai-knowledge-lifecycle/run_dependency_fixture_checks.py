"""Offline dependency-fixture contract checks; never modifies original dataset."""
import json
from pathlib import Path
from ictai.semantic58 import run
from ictai.confirmation_six import confirm_six
base=Path(__file__).resolve().parent
cases=json.loads((base/"dependency_variants.json").read_text())
expected=json.loads((base/"provisional_expected_outcomes.json").read_text())
for case in cases:
    # Independent direct confirmation from all fixture observations
    evidence=[{"tool":t,"result":v} for t,v in case["tools"].items()]
    decision=confirm_six(evidence,available_tools=case["tools"],exhausted=True)
    row=run(case,"B1_fixed",budget=12)
    want=expected[case["id"]]
    assert row["prediction"]==want, (case["id"],row)
    assert row["status"]==("CONFIRMED" if want=="DEPENDENCY_FAILURE" else "ABSTAINED"),row
    assert decision.category==want,(case["id"],decision)
    print(case["id"],row["status"],row["prediction"],"tools",row["tool_calls"])
print("DEPENDENCY FIXTURE CONTRACTS: PASS (4 variants; no API calls)")
