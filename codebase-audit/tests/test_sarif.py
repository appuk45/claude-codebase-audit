from engine.sarif import to_sarif

RESULTS = [
    {"audit": "security", "iso_characteristic": "Security",
     "checklist": [{"id": "sec_injection", "label": "No injection", "status": "fail",
                    "affected_count": 1}],
     "findings": [{"checklist_id": "sec_injection", "file": "a.py", "line": 27,
                   "severity": "High", "title": "SQL injection",
                   "recommendation": "parameterize",
                   "compliance_refs": ["OWASP A05:2025", "CWE-89"]}]},
]

def test_sarif_shape():
    doc = to_sarif(RESULTS)
    assert doc["version"] == "2.1.0"
    assert doc["runs"][0]["tool"]["driver"]["name"] == "codebase-audit"

def test_sarif_rule_and_result():
    doc = to_sarif(RESULTS)
    run = doc["runs"][0]
    rule_ids = [r["id"] for r in run["tool"]["driver"]["rules"]]
    assert "sec_injection" in rule_ids
    res = run["results"][0]
    assert res["ruleId"] == "sec_injection"
    assert res["level"] == "error"
    assert res["locations"][0]["physicalLocation"]["artifactLocation"]["uri"] == "a.py"
    assert res["locations"][0]["physicalLocation"]["region"]["startLine"] == 27
    assert "partialFingerprints" in res

def test_sarif_severity_levels():
    def one(sev):
        r = [{"audit": "x", "checklist": [],
              "findings": [{"checklist_id": "c", "file": "f", "line": 1, "severity": sev,
                            "title": "t", "recommendation": "r"}]}]
        return to_sarif(r)["runs"][0]["results"][0]["level"]
    assert one("High") == "error"
    assert one("Medium") == "warning"
    assert one("Low") == "note"
    assert one("Info") == "note"
