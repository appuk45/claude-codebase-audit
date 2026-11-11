"""A dimension that fails to run must never look like a clean pass (fail-closed gate)."""
import json
import subprocess
import sys
from pathlib import Path

from engine.gate import count_severities, errored_dimensions, evaluate_gate
from engine.html import render_html
from engine.report_md import render_markdown
from engine.sarif import to_sarif
from engine.scoring import overall_score, score_dimension
from engine.validate import error_result, load_results_dir

ROOT = Path(__file__).parents[1]
SCRIPTS = ROOT / "skills" / "codebase-audit" / "scripts"
GATE = {"max_high": 0, "max_medium": None, "max_low": None}

CLEAN = {"audit": "performance", "score": 0, "iso_characteristic": "Performance Efficiency",
         "checklist": [{"id": "perf_x", "label": "x", "status": "pass"}], "findings": []}


def test_errored_dimension_scores_none_not_ten():
    failed = error_result("security", "subagent failed")
    assert score_dimension(failed, 5000) is None
    assert overall_score([score_dimension(CLEAN, 5000), score_dimension(failed, 5000)]) == 10.0


def test_gate_fails_closed_on_errored_dimension_by_default():
    results = [CLEAN, error_result("security", "subagent failed")]
    errored = errored_dimensions(results)
    assert errored == ["security"]
    assert evaluate_gate(count_severities(results), GATE, errored) == [
        ("Errored-dimension", 1, 0)]


def test_gate_can_opt_out_of_failing_on_errors():
    errored = ["security"]
    cfg = {**GATE, "fail_on_error": False}
    assert evaluate_gate(count_severities([CLEAN]), cfg, errored) == []


def test_load_results_dir_records_invalid_and_missing(tmp_path):
    (tmp_path / "performance.json").write_text(json.dumps(CLEAN))
    (tmp_path / "security.json").write_text("{not json")
    (tmp_path / "api.json").write_text(json.dumps({"audit": "api"}))   # schema-invalid
    results = load_results_dir(tmp_path, ["performance", "security", "api", "i18n"])
    by_key = {r["audit"]: r for r in results}
    assert set(by_key) == {"performance", "security", "api", "i18n"}
    assert "error" not in by_key["performance"]
    assert "invalid result file" in by_key["security"]["error"]
    assert "invalid result file" in by_key["api"]["error"]
    assert "no result produced" in by_key["i18n"]["error"]
    assert by_key["i18n"]["iso_characteristic"] == "Portability"


def test_reports_label_errored_dimensions(tmp_path):
    results = [CLEAN, error_result("security", "subagent failed")]
    per_dim = {r["audit"]: score_dimension(r, 1000) for r in results}
    md = render_markdown(results, per_dim, overall_score(list(per_dim.values())),
                         count_severities(results))
    assert "| security | Security | ERROR |" in md
    assert "Dimensions that did not run" in md
    html = render_html(results, per_dim, 10.0, count_severities(results), {"project": "p"},
                       chartjs_source="/*chart*/")
    assert "ERROR" in html and "subagent failed" in html
    assert '"scores": [10.0, null]' in html          # radar gap, not a fake 0
    sarif = to_sarif(results)
    inv = sarif["runs"][0]["invocations"][0]
    assert inv["executionSuccessful"] is False
    assert "security" in inv["toolExecutionNotifications"][0]["message"]["text"]


def test_html_data_cannot_close_script_tag():
    evil = dict(CLEAN, audit="</script><img src=x>")
    html = render_html([evil], {evil["audit"]: 10.0}, 10.0, count_severities([evil]),
                       {"project": "p"}, chartjs_source="/*chart*/")
    assert "</script><img" not in html


def test_cli_results_dir_missing_dimension_fails_ci(tmp_path):
    rdir = tmp_path / "results"
    rdir.mkdir()
    (rdir / "performance.json").write_text(json.dumps(CLEAN))
    out = tmp_path / "audit-report.md"
    cmd = [sys.executable, str(SCRIPTS / "run_engine.py"),
           "--results-dir", str(rdir), "--expect", "performance,security",
           "--out", str(out), "--total-lines", "1000", "--ci"]
    proc = subprocess.run(cmd, cwd=tmp_path, capture_output=True, text=True)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "did not run" in proc.stdout
    assert "ERROR" in out.read_text()


def test_run_engine_entrypoint_works_from_any_cwd(tmp_path):
    (tmp_path / "r").mkdir()
    (tmp_path / "r" / "performance.json").write_text(json.dumps(CLEAN))
    cmd = [sys.executable, str(SCRIPTS / "run_engine.py"), "--results-dir", "r",
           "--out", "audit-report.md", "--formats", "md,sarif,html", "--total-lines", "100"]
    proc = subprocess.run(cmd, cwd=tmp_path, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    for name in ("audit-report.md", "audit-report.sarif", "audit-report.html"):
        assert (tmp_path / name).exists()
