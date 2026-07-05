import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parents[2]

RESULTS = [
    {"audit": "security", "score": 0, "iso_characteristic": "Security",
     "checklist": [{"id": "sec_injection", "label": "x", "status": "fail",
                    "affected_count": 1}],
     "findings": [{"checklist_id": "sec_injection", "file": "a.py", "line": 27,
                   "severity": "High", "title": "SQL injection",
                   "recommendation": "parameterize"}]},
]

def _run(tmp_path, gate_cfg=None, args=()):
    rpath = tmp_path / "results.json"
    rpath.write_text(json.dumps(RESULTS))
    out = tmp_path / "report.md"
    cfg_args = []
    if gate_cfg is not None:
        cpath = tmp_path / "cfg.yml"
        cpath.write_text(gate_cfg)
        cfg_args = ["--config", str(cpath)]
    cmd = [sys.executable, "-m", "engine.cli",
           "--results", str(rpath), "--out", str(out),
           "--total-lines", "1000", *cfg_args, *args]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    return proc, out

def test_cli_writes_report_and_passes_without_gate(tmp_path):
    proc, out = _run(tmp_path)
    assert proc.returncode == 0
    assert "SQL injection" in out.read_text()

def test_cli_gate_fails_on_high(tmp_path):
    cfg = "gate:\n  max_high: 0\n  max_medium: 10\n  max_low: null\n"
    proc, out = _run(tmp_path, gate_cfg=cfg, args=["--ci"])
    assert proc.returncode == 1
    assert "High" in proc.stdout

def test_cli_emits_sarif_and_html(tmp_path):
    rpath = tmp_path / "results.json"
    rpath.write_text(json.dumps(RESULTS))
    md = tmp_path / "r.md"
    sarif = tmp_path / "r.sarif"
    htmlf = tmp_path / "r.html"
    cmd = [sys.executable, "-m", "engine.cli",
           "--results", str(rpath), "--out", str(md),
           "--total-lines", "1000", "--formats", "md,sarif,html",
           "--sarif-out", str(sarif), "--html-out", str(htmlf)]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    assert proc.returncode == 0
    assert md.exists() and sarif.exists() and htmlf.exists()
    sdoc = json.loads(sarif.read_text())
    assert sdoc["version"] == "2.1.0"
    assert htmlf.read_text().startswith("<!DOCTYPE html>")
