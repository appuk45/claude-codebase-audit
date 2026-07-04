import json
from pathlib import Path
import pytest
from engine.validate import load_results, ValidationFailure

FIXTURE = {
    "audit": "security", "score": 0, "iso_characteristic": "Security",
    "checklist": [{"id": "sec_injection", "label": "x", "status": "pass", "affected_count": 0}],
    "findings": [],
}

def test_load_valid(tmp_path):
    p = tmp_path / "r.json"
    p.write_text(json.dumps([FIXTURE]))
    results = load_results(p)
    assert results[0]["audit"] == "security"

def test_load_invalid_raises(tmp_path):
    bad = json.loads(json.dumps(FIXTURE))
    bad["checklist"][0]["status"] = "skip"
    p = tmp_path / "r.json"
    p.write_text(json.dumps([bad]))
    with pytest.raises(ValidationFailure):
        load_results(p)
