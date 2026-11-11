from engine.scoring import (
    dimension_score, is_fully_skipped, dimension_pass_rate,
    score_dimension, overall_score,
)

def _chk(status):
    return {"id": "x", "label": "x", "status": status, "affected_count": 0}

def test_dimension_score_penalizes_high():
    findings = [{"severity": "High"}, {"severity": "High"}]
    assert dimension_score(findings, total_lines=1000) == 6.0

def test_dimension_score_floors_at_zero():
    findings = [{"severity": "High"}] * 100
    assert dimension_score(findings, total_lines=100) == 0.0

def test_fully_skipped_detected():
    assert is_fully_skipped([_chk("skipped"), _chk("skipped")]) is True
    assert is_fully_skipped([_chk("skipped"), _chk("pass")]) is False
    assert is_fully_skipped([]) is False

def test_pass_rate_excludes_skipped():
    checklist = [_chk("pass"), _chk("pass"), _chk("skipped")]
    assert dimension_pass_rate(checklist) == 100
    assert dimension_pass_rate([_chk("skipped")]) is None

def test_score_dimension_na_when_fully_skipped():
    result = {"checklist": [_chk("skipped")], "findings": []}
    assert score_dimension(result, total_lines=1000) is None

def test_overall_excludes_na():
    assert overall_score([6.0, None, 8.0]) == 7.0
    assert overall_score([None, None]) is None
