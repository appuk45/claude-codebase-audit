from engine.html import render_html

RESULTS = [
    {"audit": "security", "iso_characteristic": "Security",
     "checklist": [{"id": "sec_injection", "label": "No injection", "status": "fail",
                    "affected_count": 1},
                   {"id": "sec_xss", "label": "No XSS", "status": "skipped",
                    "affected_count": 0}],
     "findings": [{"checklist_id": "sec_injection", "file": "a.py", "line": 27,
                   "severity": "High", "title": "SQL injection",
                   "recommendation": "parameterize",
                   "compliance_refs": ["OWASP A05:2025", "CWE-89"]}]},
    {"audit": "i18n", "iso_characteristic": "Portability",
     "checklist": [{"id": "i18n_rtl", "label": "RTL", "status": "skipped",
                    "affected_count": 0}],
     "findings": []},
]
PER_DIM = {"security": 8.0, "i18n": None}
COUNTS = {"High": 1, "Medium": 0, "Low": 0, "Info": 0}
META = {"project": "demo", "date": "2026-07-05"}


def test_html_is_self_contained_and_complete():
    out = render_html(RESULTS, PER_DIM, overall=8.0, counts=COUNTS, meta=META,
                      chartjs_source="/* chartjs */")
    assert out.startswith("<!DOCTYPE html>")
    assert "demo" in out and "2026-07-05" in out
    assert "[PLACEHOLDER" not in out and "{{" not in out


def test_html_renders_na_and_skipped_and_compliance():
    out = render_html(RESULTS, PER_DIM, overall=8.0, counts=COUNTS, meta=META,
                      chartjs_source="")
    assert "N/A" in out
    assert "⏭️" in out
    assert "OWASP A05:2025" in out
    assert "SQL injection" in out


def test_html_escapes_content():
    r = [{"audit": "x", "iso_characteristic": "X", "checklist": [],
          "findings": [{"checklist_id": "c", "file": "a.py", "line": 1, "severity": "High",
                        "title": "<script>alert(1)</script>", "recommendation": "fix"}]}]
    out = render_html(r, {"x": 1.0}, overall=1.0,
                      counts={"High": 1, "Medium": 0, "Low": 0, "Info": 0},
                      meta=META, chartjs_source="")
    assert "<script>alert(1)</script>" not in out
    assert "&lt;script&gt;" in out
