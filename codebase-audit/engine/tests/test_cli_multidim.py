import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parents[2]

def test_multidim_run_excludes_na_and_gates(tmp_path):
    src = ROOT / "test-fixture" / "expected" / "multi_dim_results.json"
    out = tmp_path / "report.md"
    cfg = tmp_path / "cfg.yml"
    cfg.write_text("gate:\n  max_high: 0\n  max_medium: 10\n  max_low: null\n")
    cmd = [sys.executable, "-m", "engine.cli",
           "--results", str(src), "--out", str(out),
           "--total-lines", "1000", "--config", str(cfg), "--ci"]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    assert proc.returncode == 1
    assert "High" in proc.stdout
    report = out.read_text()
    assert "N/A" in report
    assert "security" in report and "performance" in report and "i18n" in report

def test_multidim_overall_excludes_skipped(tmp_path):
    sys.path.insert(0, str(ROOT))
    from engine.scoring import score_dimension, overall_score
    results = json.loads((ROOT / "test-fixture" / "expected" / "multi_dim_results.json").read_text())
    scores = [score_dimension(r, total_lines=1000) for r in results]
    assert scores == [8.0, 9.2, None]
    assert overall_score(scores) == 8.6
