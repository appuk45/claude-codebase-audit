import json
from pathlib import Path
from engine.validate import load_results
from engine.scoring import score_dimension
from engine.gate import count_severities, evaluate_gate

ROOT = Path(__file__).parents[2]

def test_expected_security_is_schema_valid(tmp_path):
    expected = json.loads((ROOT / "test-fixture" / "expected" / "security.json").read_text())
    p = tmp_path / "r.json"
    p.write_text(json.dumps([expected]))
    results = load_results(p)               # raises if invalid
    assert results[0]["audit"] == "security"

def test_expected_security_scores_low_and_gate_fails():
    expected = json.loads((ROOT / "test-fixture" / "expected" / "security.json").read_text())
    score = score_dimension(expected, total_lines=34)   # tiny fixture, 3 High -> floored 0
    assert score == 0.0
    counts = count_severities([expected])
    assert counts["High"] == 3
    breaches = evaluate_gate(counts, {"max_high": 0, "max_medium": None, "max_low": None})
    assert breaches == [("High", 3, 0)]
