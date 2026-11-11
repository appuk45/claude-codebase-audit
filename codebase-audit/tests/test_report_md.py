from engine.report_md import render_markdown

RESULTS = [
    {"audit": "security", "iso_characteristic": "Security",
     "checklist": [{"id": "sec_injection", "label": "No injection", "status": "fail",
                    "affected_count": 1}],
     "findings": [{"checklist_id": "sec_injection", "file": "a.py", "line": 27,
                   "severity": "High", "title": "SQL injection",
                   "recommendation": "parameterize"}]},
]

def test_markdown_has_scores_and_findings():
    md = render_markdown(RESULTS, per_dim_scores={"security": 6.0}, overall=6.0,
                         counts={"High": 1, "Medium": 0, "Low": 0, "Info": 0})
    assert "# Codebase Audit Report" in md
    assert "6.0" in md
    assert "security" in md
    assert "SQL injection" in md
    assert "a.py:27" in md

def test_markdown_shows_na_for_skipped_dim():
    md = render_markdown(RESULTS, per_dim_scores={"security": None}, overall=None,
                         counts={"High": 0, "Medium": 0, "Low": 0, "Info": 0})
    assert "N/A" in md
