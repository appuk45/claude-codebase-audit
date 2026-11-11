from engine.gate import count_severities, apply_suppressions, evaluate_gate

def _f(sev, cid="sec_x", file="a.py"):
    return {"severity": sev, "checklist_id": cid, "file": file}

RESULTS = [
    {"audit": "security", "findings": [_f("High"), _f("Medium"), _f("Low")]},
    {"audit": "perf", "findings": [_f("High", "perf_x", "b.py")]},
]

def test_count_severities():
    assert count_severities(RESULTS) == {"High": 2, "Medium": 1, "Low": 1, "Info": 0}

def test_apply_suppressions_removes_matching():
    supp = ["sec_x@a.py"]
    out = apply_suppressions(RESULTS, supp)
    counts = count_severities(out)
    assert counts == {"High": 1, "Medium": 0, "Low": 0, "Info": 0}

def test_gate_breach_on_high():
    counts = {"High": 2, "Medium": 1, "Low": 1, "Info": 0}
    breaches = evaluate_gate(counts, {"max_high": 0, "max_medium": 10, "max_low": None})
    assert breaches == [("High", 2, 0)]

def test_gate_pass_when_within_limits():
    counts = {"High": 0, "Medium": 3, "Low": 50, "Info": 0}
    breaches = evaluate_gate(counts, {"max_high": 0, "max_medium": 10, "max_low": None})
    assert breaches == []
