import json
from pathlib import Path
import jsonschema

SCHEMA = json.loads((Path(__file__).parents[2] / "shared" / "schema.json").read_text())

VALID = {
    "audit": "security",
    "score": 0,
    "iso_characteristic": "Security",
    "checklist": [
        {"id": "sec_injection", "label": "No injection", "status": "fail", "affected_count": 1}
    ],
    "findings": [
        {"checklist_id": "sec_injection", "file": "a.py", "line": 27, "severity": "High",
         "title": "SQL injection", "detail": "concatenated query",
         "recommendation": "parameterize", "compliance_refs": ["OWASP A05:2025"]}
    ],
}

def test_valid_result_passes():
    jsonschema.validate(VALID, SCHEMA)

def test_bad_status_rejected():
    bad = json.loads(json.dumps(VALID))
    bad["checklist"][0]["status"] = "skip"   # not the canonical "skipped"
    try:
        jsonschema.validate(bad, SCHEMA)
        assert False, "should have rejected status 'skip'"
    except jsonschema.ValidationError:
        pass

def test_bad_severity_rejected():
    bad = json.loads(json.dumps(VALID))
    bad["findings"][0]["severity"] = "Critical"   # not in enum
    try:
        jsonschema.validate(bad, SCHEMA)
        assert False, "should have rejected severity 'Critical'"
    except jsonschema.ValidationError:
        pass
