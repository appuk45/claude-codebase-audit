# Codebase Audit — Foundation + Vertical Slice Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the shared foundation + a deterministic scoring/gate/report engine + one working dimension skill (security) + a minimal orchestrator, so `/codebase-audit` runs end-to-end on a fixture and emits a markdown report with a correct CI exit code.

**Architecture:** Detection is LLM-driven — the orchestrator dispatches parallel Agent subagents, each reading one bundled `shared/detection/NN-*.md` spec and emitting `AuditResult` JSON (validated against `shared/schema.json`). All deterministic work (schema validation, per-dimension + overall scoring with skip-exclusion, CI gate on raw severity counts, markdown rendering) lives in a small tested Python package `engine/`, invoked by the orchestrator via `python -m engine.cli`. SARIF, HTML, and compliance-map join come in Plan 3.

**Tech Stack:** Python 3.11+, `jsonschema` (validation), `PyYAML` (config), `pytest` (tests). Claude Code plugin structure (`.claude-plugin/plugin.json`, `skills/`, `shared/`). The 11 detection specs already exist under `codebase-audit/shared/detection/`.

---

## File Structure

Plugin root is `codebase-audit/` (already contains `shared/detection/*`).

- Create: `codebase-audit/.claude-plugin/plugin.json` — plugin manifest.
- Create: `codebase-audit/shared/schema.json` — JSON Schema for `AuditResult` (the contract all dims emit).
- Create: `codebase-audit/shared/discovery.md` — discovery + archetype classification instructions.
- Create: `codebase-audit/shared/scoring.md` — human-readable scoring + gate rules (points at the engine).
- Create: `codebase-audit/shared/config-schema.md` — `.codebase-audit.yml` spec.
- Create: `codebase-audit/engine/__init__.py`
- Create: `codebase-audit/engine/validate.py` — load + schema-validate AuditResult JSON.
- Create: `codebase-audit/engine/scoring.py` — per-dimension + overall score, skip-exclusion, pass-rate.
- Create: `codebase-audit/engine/gate.py` — severity counts, suppressions, gate evaluation.
- Create: `codebase-audit/engine/report_md.py` — markdown report renderer.
- Create: `codebase-audit/engine/cli.py` — entrypoint wiring validate → score → gate → report → exit code.
- Create: `codebase-audit/engine/tests/` — pytest suite for the above.
- Create: `codebase-audit/skills/audit-security/SKILL.md` — thin security dimension skill.
- Create: `codebase-audit/skills/codebase-audit/SKILL.md` — minimal orchestrator.
- Create: `codebase-audit/test-fixture/bad_views.py` — planted-vuln fixture (from draft).
- Create: `codebase-audit/test-fixture/expected/security.json` — expected security AuditResult.
- Create: `codebase-audit/requirements-dev.txt` — jsonschema, PyYAML, pytest.

Each `engine/` module has one responsibility; the CLI composes them. Detection stays out of the engine (it's LLM work).

---

## Task 1: Plugin scaffold

**Files:**
- Create: `codebase-audit/.claude-plugin/plugin.json`
- Create: `codebase-audit/requirements-dev.txt`

- [ ] **Step 1: Write the plugin manifest**

`codebase-audit/.claude-plugin/plugin.json`:
```json
{
  "name": "codebase-audit",
  "version": "0.1.0",
  "description": "Multi-dimension enterprise codebase audit: 11 dimension skills + orchestrator, SARIF/CI-gate/HTML, ISO 25010.",
  "author": "Appu K"
}
```

- [ ] **Step 2: Write dev requirements**

`codebase-audit/requirements-dev.txt`:
```
jsonschema>=4.0
PyYAML>=6.0
pytest>=7.0
```

- [ ] **Step 3: Install dev deps**

Run: `pip install -r codebase-audit/requirements-dev.txt`
Expected: installs jsonschema, PyYAML, pytest successfully.

- [ ] **Step 4: Commit**

```bash
git add codebase-audit/.claude-plugin/plugin.json codebase-audit/requirements-dev.txt
git commit -m "chore: plugin scaffold + dev requirements"
```

---

## Task 2: AuditResult JSON schema

**Files:**
- Create: `codebase-audit/shared/schema.json`
- Test: `codebase-audit/engine/tests/test_schema.py`

- [ ] **Step 1: Write the failing test**

`codebase-audit/engine/tests/test_schema.py`:
```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest codebase-audit/engine/tests/test_schema.py -v`
Expected: FAIL — `shared/schema.json` does not exist yet.

- [ ] **Step 3: Write the schema**

`codebase-audit/shared/schema.json`:
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "AuditResult",
  "type": "object",
  "required": ["audit", "score", "iso_characteristic", "checklist", "findings"],
  "additionalProperties": true,
  "properties": {
    "audit": {"type": "string"},
    "score": {"type": ["number", "null"]},
    "iso_characteristic": {"type": "string"},
    "archetypes_applied": {"type": "array", "items": {"type": "string"}},
    "error": {"type": "string"},
    "checklist": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "label", "status"],
        "additionalProperties": false,
        "properties": {
          "id": {"type": "string"},
          "label": {"type": "string"},
          "status": {"enum": ["pass", "fail", "warning", "skipped"]},
          "affected_count": {"type": "integer", "minimum": 0}
        }
      }
    },
    "findings": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["checklist_id", "file", "severity", "title", "recommendation"],
        "additionalProperties": true,
        "properties": {
          "checklist_id": {"type": "string"},
          "file": {"type": "string"},
          "line": {"type": ["integer", "string", "null"]},
          "severity": {"enum": ["High", "Medium", "Low", "Info"]},
          "title": {"type": "string"},
          "detail": {"type": "string"},
          "recommendation": {"type": "string"},
          "compliance_refs": {"type": "array", "items": {"type": "string"}}
        }
      }
    }
  }
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest codebase-audit/engine/tests/test_schema.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add codebase-audit/shared/schema.json codebase-audit/engine/tests/test_schema.py
git commit -m "feat: AuditResult JSON schema + validation tests"
```

---

## Task 3: Engine — result loading & validation

**Files:**
- Create: `codebase-audit/engine/__init__.py`
- Create: `codebase-audit/engine/validate.py`
- Test: `codebase-audit/engine/tests/test_validate.py`

- [ ] **Step 1: Create the package init**

`codebase-audit/engine/__init__.py`:
```python
"""Deterministic scoring/gate/report engine for codebase-audit."""
```

- [ ] **Step 2: Write the failing test**

`codebase-audit/engine/tests/test_validate.py`:
```python
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
```

- [ ] **Step 3: Write the implementation**

`codebase-audit/engine/validate.py`:
```python
import json
from pathlib import Path
import jsonschema

_SCHEMA = json.loads((Path(__file__).parent.parent / "shared" / "schema.json").read_text())


class ValidationFailure(Exception):
    """Raised when an AuditResult fails schema validation."""


def load_results(path):
    """Load a JSON array of AuditResult objects and validate each against the schema."""
    data = json.loads(Path(path).read_text())
    if not isinstance(data, list):
        raise ValidationFailure("results file must be a JSON array of AuditResult objects")
    for i, result in enumerate(data):
        try:
            jsonschema.validate(result, _SCHEMA)
        except jsonschema.ValidationError as e:
            raise ValidationFailure(f"result[{i}] ({result.get('audit', '?')}): {e.message}")
    return data
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd codebase-audit && pytest engine/tests/test_validate.py -v`
Expected: PASS (2 tests). (Run from `codebase-audit/` so `engine` imports resolve.)

- [ ] **Step 5: Commit**

```bash
git add codebase-audit/engine/__init__.py codebase-audit/engine/validate.py codebase-audit/engine/tests/test_validate.py
git commit -m "feat: engine result loading + schema validation"
```

---

## Task 4: Engine — scoring with skip-exclusion

**Files:**
- Create: `codebase-audit/engine/scoring.py`
- Test: `codebase-audit/engine/tests/test_scoring.py`

Implements spec §9a.1: a fully-skipped dimension scores `None` (N/A) and is excluded from the overall average; per-dimension pass-rate is over applicable (non-skipped) items only.

- [ ] **Step 1: Write the failing test**

`codebase-audit/engine/tests/test_scoring.py`:
```python
from engine.scoring import (
    dimension_score, is_fully_skipped, dimension_pass_rate,
    score_dimension, overall_score,
)

def _chk(status):
    return {"id": "x", "label": "x", "status": status, "affected_count": 0}

def test_dimension_score_penalizes_high():
    findings = [{"severity": "High"}, {"severity": "High"}]
    # 10 - (2*2.0)/1000*1000 = 10 - 4 = 6.0
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
    assert dimension_pass_rate(checklist) == 100        # 2/2, skip not counted
    assert dimension_pass_rate([_chk("skipped")]) is None

def test_score_dimension_na_when_fully_skipped():
    result = {"checklist": [_chk("skipped")], "findings": []}
    assert score_dimension(result, total_lines=1000) is None

def test_overall_excludes_na():
    # scores: 6.0, None, 8.0  -> average of applicable = 7.0
    assert overall_score([6.0, None, 8.0]) == 7.0
    assert overall_score([None, None]) is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd codebase-audit && pytest engine/tests/test_scoring.py -v`
Expected: FAIL — `engine.scoring` does not exist.

- [ ] **Step 3: Write the implementation**

`codebase-audit/engine/scoring.py`:
```python
SEV_WEIGHTS = {"High": 2.0, "Medium": 0.8, "Low": 0.3, "Info": 0.0}


def dimension_score(findings, total_lines):
    """Display score 0-10 (draft formula). Lower = worse. Rounded to 1 dp."""
    penalty = sum(SEV_WEIGHTS.get(f["severity"], 0.0) for f in findings)
    raw = 10.0 - (penalty / max(total_lines, 1)) * 1000
    return round(max(0.0, min(10.0, raw)), 1)


def is_fully_skipped(checklist):
    """True when a dimension has items and every one is 'skipped' (non-applicable)."""
    return len(checklist) > 0 and all(item["status"] == "skipped" for item in checklist)


def dimension_pass_rate(checklist):
    """Pass rate over APPLICABLE (non-skipped) items only. None if none applicable."""
    applicable = [i for i in checklist if i["status"] != "skipped"]
    if not applicable:
        return None
    passed = sum(1 for i in applicable if i["status"] == "pass")
    return round(passed / len(applicable) * 100)


def score_dimension(result, total_lines):
    """Per-dimension score, or None (N/A) when the dimension is fully skipped."""
    if is_fully_skipped(result["checklist"]):
        return None
    return dimension_score(result["findings"], total_lines)


def overall_score(dimension_scores):
    """Average of applicable dimension scores; N/A dims (None) excluded. None if all N/A."""
    applicable = [s for s in dimension_scores if s is not None]
    if not applicable:
        return None
    return round(sum(applicable) / len(applicable), 1)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd codebase-audit && pytest engine/tests/test_scoring.py -v`
Expected: PASS (6 tests).

- [ ] **Step 5: Commit**

```bash
git add codebase-audit/engine/scoring.py codebase-audit/engine/tests/test_scoring.py
git commit -m "feat: engine scoring with skip-exclusion (spec 9a.1)"
```

---

## Task 5: Engine — CI gate & suppressions

**Files:**
- Create: `codebase-audit/engine/gate.py`
- Test: `codebase-audit/engine/tests/test_gate.py`

- [ ] **Step 1: Write the failing test**

`codebase-audit/engine/tests/test_gate.py`:
```python
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
    assert counts == {"High": 1, "Medium": 0, "Low": 0, "Info": 0}   # only perf High remains

def test_gate_breach_on_high():
    counts = {"High": 2, "Medium": 1, "Low": 1, "Info": 0}
    breaches = evaluate_gate(counts, {"max_high": 0, "max_medium": 10, "max_low": None})
    assert breaches == [("High", 2, 0)]

def test_gate_pass_when_within_limits():
    counts = {"High": 0, "Medium": 3, "Low": 50, "Info": 0}
    breaches = evaluate_gate(counts, {"max_high": 0, "max_medium": 10, "max_low": None})
    assert breaches == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd codebase-audit && pytest engine/tests/test_gate.py -v`
Expected: FAIL — `engine.gate` does not exist.

- [ ] **Step 3: Write the implementation**

`codebase-audit/engine/gate.py`:
```python
import copy

_SEVERITIES = ["High", "Medium", "Low", "Info"]
_GATE_KEYS = [("High", "max_high"), ("Medium", "max_medium"), ("Low", "max_low")]


def count_severities(results):
    counts = {s: 0 for s in _SEVERITIES}
    for r in results:
        for f in r.get("findings", []):
            sev = f.get("severity")
            if sev in counts:
                counts[sev] += 1
    return counts


def apply_suppressions(results, suppressions):
    """Remove findings whose 'checklist_id@file' is in the suppression list. Non-mutating."""
    supp = set(suppressions or [])
    out = copy.deepcopy(results)
    for r in out:
        r["findings"] = [
            f for f in r.get("findings", [])
            if f"{f.get('checklist_id')}@{f.get('file')}" not in supp
        ]
    return out


def evaluate_gate(counts, gate_cfg):
    """Return a list of (severity, actual, limit) breaches. Empty list = gate passes.

    A gate limit of None means 'ignore that severity'.
    """
    breaches = []
    for sev, key in _GATE_KEYS:
        limit = gate_cfg.get(key)
        if limit is not None and counts[sev] > limit:
            breaches.append((sev, counts[sev], limit))
    return breaches
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd codebase-audit && pytest engine/tests/test_gate.py -v`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add codebase-audit/engine/gate.py codebase-audit/engine/tests/test_gate.py
git commit -m "feat: engine CI gate (raw counts) + suppressions"
```

---

## Task 6: Engine — markdown report

**Files:**
- Create: `codebase-audit/engine/report_md.py`
- Test: `codebase-audit/engine/tests/test_report_md.py`

- [ ] **Step 1: Write the failing test**

`codebase-audit/engine/tests/test_report_md.py`:
```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd codebase-audit && pytest engine/tests/test_report_md.py -v`
Expected: FAIL — `engine.report_md` does not exist.

- [ ] **Step 3: Write the implementation**

`codebase-audit/engine/report_md.py`:
```python
def _fmt_score(s):
    return "N/A" if s is None else f"{s}/10"


def render_markdown(results, per_dim_scores, overall, counts):
    """Render a diff-friendly markdown report for CI logs / PR comments."""
    lines = []
    lines.append("# Codebase Audit Report")
    lines.append("")
    lines.append(f"**Overall score:** {_fmt_score(overall)}")
    lines.append("")
    lines.append(
        f"**Findings:** {counts['High']} High · {counts['Medium']} Medium · "
        f"{counts['Low']} Low · {counts['Info']} Info"
    )
    lines.append("")
    lines.append("## Dimension Scores")
    lines.append("")
    lines.append("| Dimension | ISO | Score |")
    lines.append("|---|---|---|")
    for r in results:
        name = r["audit"]
        lines.append(f"| {name} | {r.get('iso_characteristic', '')} | "
                     f"{_fmt_score(per_dim_scores.get(name))} |")
    lines.append("")
    lines.append("## Findings")
    lines.append("")
    any_findings = False
    for r in results:
        for f in r.get("findings", []):
            any_findings = True
            loc = f"{f['file']}:{f.get('line', '—')}"
            lines.append(
                f"- **[{f['severity']}]** `{loc}` — {f['title']} "
                f"({r['audit']}). _{f.get('recommendation', '')}_"
            )
    if not any_findings:
        lines.append("_No findings._")
    lines.append("")
    return "\n".join(lines)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd codebase-audit && pytest engine/tests/test_report_md.py -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add codebase-audit/engine/report_md.py codebase-audit/engine/tests/test_report_md.py
git commit -m "feat: engine markdown report renderer"
```

---

## Task 7: Engine — CLI wiring

**Files:**
- Create: `codebase-audit/engine/cli.py`
- Test: `codebase-audit/engine/tests/test_cli.py`

The CLI ties it together: load+validate results, load config, apply suppressions, score, gate, write markdown, set exit code (1 if gate breached, else 0).

- [ ] **Step 1: Write the failing test**

`codebase-audit/engine/tests/test_cli.py`:
```python
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parents[2]   # codebase-audit/

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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd codebase-audit && pytest engine/tests/test_cli.py -v`
Expected: FAIL — `engine.cli` does not exist.

- [ ] **Step 3: Write the implementation**

`codebase-audit/engine/cli.py`:
```python
import argparse
import sys
from pathlib import Path

import yaml

from engine.validate import load_results, ValidationFailure
from engine.scoring import score_dimension, overall_score
from engine.gate import count_severities, apply_suppressions, evaluate_gate
from engine.report_md import render_markdown

DEFAULT_GATE = {"max_high": 0, "max_medium": None, "max_low": None}


def _load_config(path):
    if not path:
        return {"gate": dict(DEFAULT_GATE), "suppress": []}
    cfg = yaml.safe_load(Path(path).read_text()) or {}
    gate = {**DEFAULT_GATE, **(cfg.get("gate") or {})}
    return {"gate": gate, "suppress": cfg.get("suppress") or []}


def main(argv=None):
    ap = argparse.ArgumentParser(prog="engine.cli")
    ap.add_argument("--results", required=True, help="path to AuditResult[] JSON")
    ap.add_argument("--out", required=True, help="path to write the markdown report")
    ap.add_argument("--config", help="path to .codebase-audit.yml")
    ap.add_argument("--total-lines", type=int, default=1, help="discovery_context.total_lines")
    ap.add_argument("--ci", action="store_true", help="enforce gate + set exit code")
    args = ap.parse_args(argv)

    try:
        results = load_results(args.results)
    except ValidationFailure as e:
        print(f"validation error: {e}", file=sys.stderr)
        return 2

    config = _load_config(args.config)
    gated_results = apply_suppressions(results, config["suppress"])

    per_dim = {r["audit"]: score_dimension(r, args.total_lines) for r in gated_results}
    overall = overall_score(list(per_dim.values()))
    counts = count_severities(gated_results)

    md = render_markdown(gated_results, per_dim, overall, counts)
    Path(args.out).write_text(md)

    breaches = evaluate_gate(counts, config["gate"]) if args.ci else []
    if breaches:
        for sev, actual, limit in breaches:
            print(f"GATE FAIL: {sev} findings {actual} exceed limit {limit}")
        return 1
    print(f"Audit report written to {args.out} (overall {overall})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd codebase-audit && pytest engine/tests/test_cli.py -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Run the full engine suite**

Run: `cd codebase-audit && pytest engine/ -v`
Expected: PASS (all tests across tasks 2–7).

- [ ] **Step 6: Commit**

```bash
git add codebase-audit/engine/cli.py codebase-audit/engine/tests/test_cli.py
git commit -m "feat: engine CLI wiring (validate -> score -> gate -> report)"
```

---

## Task 8: Discovery instructions (+ archetype)

**Files:**
- Create: `codebase-audit/shared/discovery.md`

No code test — this is an LLM instruction file. Verified by inspection + used live in Task 12.

- [ ] **Step 1: Write the discovery spec**

`codebase-audit/shared/discovery.md`:
````markdown
# Discovery — stack detection + archetype classification

Run these commands against the current working directory and assemble a
`discovery_context` JSON object. If a command yields nothing, record an empty
array / false. Do not skip commands.

## Commands

```bash
# Language counts
find . -name "*.py"  | grep -vE "__pycache__|\.venv" | wc -l
find . \( -name "*.ts" -o -name "*.tsx" \) | grep -v node_modules | wc -l
find . -name "*.js"  | grep -vE "node_modules|dist" | wc -l

# Framework hints
grep -rlE "from django|import django" . --include="*.py" 2>/dev/null | head -3
grep -rl "from fastapi" . --include="*.py" 2>/dev/null | head -3
grep -rl "from flask" . --include="*.py" 2>/dev/null | head -3
cat package.json 2>/dev/null

# IaC
find . \( -name "Dockerfile" -o -name "docker-compose*.y*ml" \) 2>/dev/null
find . -name "*.tf" 2>/dev/null | head -5
find . \( -path "*/k8s/*.y*ml" -o -path "*/kubernetes/*.y*ml" -o -name "*deployment*.y*ml" \) 2>/dev/null | head -5

# CI
ls .github/workflows/ 2>/dev/null; ls Jenkinsfile .gitlab-ci.yml 2>/dev/null

# Manifests + entry points
ls requirements.txt pyproject.toml poetry.lock package.json package-lock.json uv.lock 2>/dev/null
ls manage.py wsgi.py asgi.py main.py index.js server.js 2>/dev/null

# Total lines (for scoring)
find . \( -name "*.py" -o -name "*.ts" -o -name "*.tsx" -o -name "*.js" \) \
  | grep -vE "node_modules|__pycache__|\.venv|dist" | xargs wc -l 2>/dev/null | tail -1
```

## Archetype classification (spec §5a.1)

Assign one or more archetypes to `archetypes` using these heuristics:

- **web-api**: server framework (Django/FastAPI/Flask/Express/Fastify) + route/controller
  dirs, no significant frontend build.
- **frontend-spa**: React/Vue/Svelte/Angular deps + a build config (vite/webpack/next), UI
  components, no owned backend.
- **fullstack**: both a server framework AND a frontend build present.
- **cli-tool**: `__main__`, `argparse`/`click`/`commander`, a `bin`/console-scripts entry,
  output to stdout as the product.
- **library**: a published package manifest (name/version, `packages`/`exports`) with no
  server entry point.
- **data-ml**: notebooks, `pandas`/`numpy`/`torch`/`sklearn`, pipeline/training scripts.
- **worker-service**: queue/consumer frameworks (celery/rq/kafka/`@task`/consumer loops),
  long-running non-HTTP process.

## Output schema

```json
{
  "languages": ["python"],
  "framework": "django",
  "archetypes": ["web-api"],
  "file_count": 142,
  "total_lines": 8420,
  "has_docker": true,
  "has_k8s": false,
  "has_terraform": false,
  "has_iac": true,
  "has_ci": true,
  "manifest_files": ["requirements.txt", "pyproject.toml"],
  "entry_points": ["manage.py", "wsgi.py"],
  "context": { "maturity": "production" }
}
```

`context.maturity` defaults to `production`; override from `.codebase-audit.yml`.
````

- [ ] **Step 2: Verify the commands run**

Run: `cd codebase-audit && bash -n <(sed -n '/```bash/,/```/p' shared/discovery.md | sed '1d;$d')`
Expected: no syntax errors (bash parse check of the command block).

- [ ] **Step 3: Commit**

```bash
git add codebase-audit/shared/discovery.md
git commit -m "feat: discovery + archetype classification spec"
```

---

## Task 9: Scoring & config docs

**Files:**
- Create: `codebase-audit/shared/scoring.md`
- Create: `codebase-audit/shared/config-schema.md`

- [ ] **Step 1: Write the scoring doc**

`codebase-audit/shared/scoring.md`:
````markdown
# Scoring & CI Gating (authoritative rules; implemented in `engine/`)

## Display score (per dimension)
`score = max(0, min(10, 10 − (H×2.0 + M×0.8 + L×0.3) / max(total_lines, 1) × 1000))`,
rounded to 1 dp. Info findings carry weight 0. **Display only** — labeled "indicative".

## Skip handling (spec §9a.1)
- A **fully-skipped** dimension (every checklist item `skipped`) scores **N/A** and is
  **excluded** from the overall average — it does NOT contribute a 10.
- **Overall score** = average of applicable (non-N/A) dimension scores.
- **Pass rate** per dimension = `passed / (total − skipped)` — applicable items only.

## CI gate (authoritative — NOT the score)
Count raw severities across all dimensions; compare to config thresholds. A `null`
threshold means ignore. Suppressions (`checklist_id@file`) are removed before counting.
Any breach → exit 1; otherwise exit 0. Implemented in `engine/gate.py`.

The engine is the single source of these computations; skills must call
`python -m engine.cli`, never re-implement the math.
````

- [ ] **Step 2: Write the config doc**

`codebase-audit/shared/config-schema.md`:
````markdown
# `.codebase-audit.yml` — configuration

```yaml
# Which dimensions to run (default: all applicable)
dimensions: [security, performance]      # omit for all

# Project maturity — adjusts context-severity modifiers
context:
  maturity: production                   # prototype | internal | production | enterprise

# Paths to ignore during detection
ignore:
  - "**/migrations/**"
  - "**/node_modules/**"

# CI gate thresholds (raw severity counts; null = ignore)
gate:
  max_high: 0
  max_medium: 10
  max_low: null

# Suppress specific findings (checklist_id@file)
suppress:
  - sec_weak_crypto@legacy/old_hash.py
```

Precedence: CLI flags > `.codebase-audit.yml` > defaults.
````

- [ ] **Step 3: Commit**

```bash
git add codebase-audit/shared/scoring.md codebase-audit/shared/config-schema.md
git commit -m "docs: scoring rules + config schema"
```

---

## Task 10: Test fixture + expected result

**Files:**
- Create: `codebase-audit/test-fixture/bad_views.py`
- Create: `codebase-audit/test-fixture/expected/security.json`
- Test: `codebase-audit/engine/tests/test_fixture_expected.py`

- [ ] **Step 1: Write the planted-vuln fixture**

`codebase-audit/test-fixture/bad_views.py`:
```python
import requests
from django.http import JsonResponse

# TODO: fix this later
# FIXME: this is broken

SECRET_KEY = "hardcoded-secret-abc123"
DATABASE_URL = "postgres://admin:password@localhost/mydb"


async def get_orders(request):
    orders = Order.objects.all()          # no pagination + N+1 below
    for order in orders:
        items = order.items.all()         # N+1
    response = requests.get("http://external-api.com/data")   # blocking in async
    return JsonResponse({"orders": list(orders)})


def admin_panel(request):                 # no auth guard
    users = User.objects.all()
    return JsonResponse({"users": list(users)})


def execute_query(request):
    name = request.GET.get("name")
    cursor.execute("SELECT * FROM users WHERE name = '" + name + "'")   # SQL injection
    return JsonResponse({})


try:
    risky_operation()
except:                                    # bare except, multi-line swallow
    pass
```

- [ ] **Step 2: Write the expected security result**

`codebase-audit/test-fixture/expected/security.json`:
```json
{
  "audit": "security",
  "score": 0,
  "iso_characteristic": "Security",
  "archetypes_applied": ["web-api"],
  "checklist": [
    {"id": "sec_access_control", "label": "Auth guard on sensitive routes", "status": "fail", "affected_count": 1},
    {"id": "sec_injection", "label": "No injection", "status": "fail", "affected_count": 1},
    {"id": "sec_hardcoded_secrets", "label": "No secrets in source", "status": "fail", "affected_count": 1}
  ],
  "findings": [
    {"checklist_id": "sec_injection", "file": "test-fixture/bad_views.py", "line": 30,
     "severity": "High", "title": "SQL injection via string concatenation",
     "detail": "User input concatenated into SQL.", "recommendation": "Use parameterized queries.",
     "compliance_refs": ["OWASP A05:2025", "CWE-89"]},
    {"checklist_id": "sec_hardcoded_secrets", "file": "test-fixture/bad_views.py", "line": 7,
     "severity": "High", "title": "Hardcoded SECRET_KEY",
     "detail": "Secret literal in source.", "recommendation": "Load from environment.",
     "compliance_refs": ["OWASP A04:2025", "CWE-798"]},
    {"checklist_id": "sec_access_control", "file": "test-fixture/bad_views.py", "line": 20,
     "severity": "High", "title": "Admin route without auth guard",
     "detail": "admin_panel has no auth decorator.", "recommendation": "Add auth middleware.",
     "compliance_refs": ["OWASP A01:2025", "CWE-862"]}
  ]
}
```

- [ ] **Step 3: Write the test that runs expected through the engine**

`codebase-audit/engine/tests/test_fixture_expected.py`:
```python
import json
from pathlib import Path
from engine.validate import load_results
from engine.scoring import score_dimension
from engine.gate import count_severities, evaluate_gate

ROOT = Path(__file__).parents[2]

def test_expected_security_is_schema_valid(tmp_path):
    expected = json.loads((ROOT / "test-fixture" / "expected" / "security.json").read_text())
    p = tmp_path / "r.json"
    p.write_text(json.dumps([expected]))
    results = load_results(p)               # raises if invalid
    assert results[0]["audit"] == "security"

def test_expected_security_scores_low_and_gate_fails():
    expected = json.loads((ROOT / "test-fixture" / "expected" / "security.json").read_text())
    score = score_dimension(expected, total_lines=34)   # tiny fixture, 3 High -> floored 0
    assert score == 0.0
    counts = count_severities([expected])
    assert counts["High"] == 3
    breaches = evaluate_gate(counts, {"max_high": 0, "max_medium": None, "max_low": None})
    assert breaches == [("High", 3, 0)]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd codebase-audit && pytest engine/tests/test_fixture_expected.py -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Validate the security signals actually locate the fixture vulns**

Run:
```bash
cd codebase-audit/test-fixture
rg -n "cursor\.execute\(.*\+" bad_views.py           # sec_injection candidate
rg -n "(secret|key)\s*=\s*['\"]" -i bad_views.py     # sec_hardcoded_secrets candidate
rg -n "def admin_panel" bad_views.py                 # sec_access_control candidate
```
Expected: each command returns the corresponding planted line. (Confirms `02-security.md`
signals resolve the expected findings.)

- [ ] **Step 6: Commit**

```bash
git add codebase-audit/test-fixture/ codebase-audit/engine/tests/test_fixture_expected.py
git commit -m "test: planted-vuln fixture + expected security result"
```

---

## Task 11: Security dimension skill (thin)

**Files:**
- Create: `codebase-audit/skills/audit-security/SKILL.md`

Instruction file — no unit test; exercised live in Task 12. Follows the dimension contract
(spec §5): discovery-if-standalone → filter by archetype → two-stage grep-first detection →
emit AuditResult JSON validated against the schema.

- [ ] **Step 1: Write the skill**

`codebase-audit/skills/audit-security/SKILL.md`:
````markdown
---
name: audit-security
description: Security dimension audit (OWASP 2025) — emits AuditResult JSON; runs standalone or as an orchestrator subagent.
---

# /audit-security

Audit the current working directory for the Security dimension.

## Inputs
- Optional `discovery_context` (JSON) injected by the orchestrator.
- Flags: `--json` (emit JSON only, no markdown summary).

## Steps

1. **Discovery**: if `discovery_context` was NOT injected, run `shared/discovery.md` and
   build it. If injected, use it as-is (do not re-run discovery).
2. **Filter**: read `shared/detection/02-security.md`. Drop any checklist item whose
   `applies_to` shares no archetype with `discovery_context.archetypes` → emit it with
   `status: "skipped"`.
3. **Detect (two-stage, spec §5a.2 / §9a.4)**:
   a. For each applicable item, run its `signals` (ripgrep) to get candidate `file:line`.
      Prefer bandit/semgrep output if available. Do NOT read the whole repo.
   b. Read only candidate snippets; apply each item's `confirm` rule with taint reasoning
      (is the value user-controlled?). Assign severity honoring the High floors.
      Consult `shared/detection/examples/02-security.md` only when a candidate is ambiguous.
4. **Emit**: produce one `AuditResult` JSON object conforming to `shared/schema.json` with
   `audit: "security"`, `iso_characteristic: "Security"`, the checklist (with statuses), and
   findings. Leave `score` as `0` — the engine computes it.
   - With `--json` or as a subagent: output ONLY the JSON.
   - Standalone: also print a short markdown summary (counts + top findings).

Return only valid JSON when invoked as a subagent.
````

- [ ] **Step 2: Verify frontmatter + referenced files exist**

Run:
```bash
cd codebase-audit
test -f shared/detection/02-security.md && test -f shared/detection/examples/02-security.md \
  && test -f shared/schema.json && echo OK
```
Expected: prints `OK`.

- [ ] **Step 3: Commit**

```bash
git add codebase-audit/skills/audit-security/SKILL.md
git commit -m "feat: audit-security dimension skill (thin)"
```

---

## Task 12: Minimal orchestrator

**Files:**
- Create: `codebase-audit/skills/codebase-audit/SKILL.md`

Vertical slice: discovery → dispatch the security subagent → collect JSON → call the engine →
markdown + exit code. (Menu, remaining dims, HTML/SARIF come in Plans 2–3.)

- [ ] **Step 1: Write the orchestrator skill**

`codebase-audit/skills/codebase-audit/SKILL.md`:
````markdown
---
name: codebase-audit
description: Orchestrates the multi-dimension codebase audit — discovery, parallel dimension subagents, deterministic scoring/gate, report output.
---

# /codebase-audit

Run a multi-dimension static audit of the current working directory.

```
/codebase-audit [--ci] [--config PATH]
```

Plan-1 scope: runs the Security dimension end-to-end. (Additional dimensions and HTML/SARIF
outputs are added by later plans.)

## Steps

1. **Config**: if `--config` given or `.codebase-audit.yml` exists, load it (see
   `shared/config-schema.md`). Otherwise use defaults.
2. **Discovery**: run `shared/discovery.md` ONCE. Build `discovery_context` (including
   `archetypes` and `total_lines`). Print:
   `Discovered: [languages] | archetypes: [...] | files: [n]`.
3. **Dispatch**: launch the `audit-security` work as a subagent (Agent tool), passing
   `discovery_context` and instructing it to read `shared/detection/02-security.md` and emit
   AuditResult JSON only. (This is the parallel path; with more dimensions, dispatch them
   concurrently.)
4. **Collect**: gather the AuditResult JSON object(s) into a JSON array; write it to
   `/tmp/codebase-audit-results.json`.
5. **Engine**: run
   ```bash
   python -m engine.cli \
     --results /tmp/codebase-audit-results.json \
     --out audit-report.md \
     --total-lines <discovery_context.total_lines> \
     [--config <path>] [--ci]
   ```
   from the plugin directory (so `engine` imports resolve). The engine validates, scores
   (with skip-exclusion), gates, and writes `audit-report.md`. In `--ci` mode its exit code
   is the gate result.
6. **Report**: print the engine's stdout and the path to `audit-report.md`. In `--ci` mode,
   propagate the engine exit code.

Do not compute scores or gate logic yourself — the engine owns that (`shared/scoring.md`).
````

- [ ] **Step 2: End-to-end dry run of the engine path**

Create a results file from the expected fixture and run the engine exactly as the
orchestrator would:
```bash
cd codebase-audit
python -c "import json,sys; d=json.load(open('test-fixture/expected/security.json')); json.dump([d], open('/tmp/ca-results.json','w'))"
python -m engine.cli --results /tmp/ca-results.json --out /tmp/ca-report.md --total-lines 34 --ci; echo "exit=$?"
```
Expected: prints `GATE FAIL: High findings 3 exceed limit 0`, `exit=1`, and
`/tmp/ca-report.md` contains the three High findings + `N/A`-free security score `0/10`.

- [ ] **Step 3: Commit**

```bash
git add codebase-audit/skills/codebase-audit/SKILL.md
git commit -m "feat: minimal orchestrator (discovery -> security subagent -> engine)"
```

---

## Task 13: Final verification

- [ ] **Step 1: Run the whole engine test suite**

Run: `cd codebase-audit && pytest engine/ -v`
Expected: PASS — all tests from Tasks 2–10.

- [ ] **Step 2: Confirm no unexpanded placeholders in skills/docs**

Run:
```bash
cd codebase-audit
rg -n "TBD|TODO: implement|FIXME: fill" skills/ shared/scoring.md shared/config-schema.md \
  shared/discovery.md || echo "clean"
```
Expected: prints `clean`.

- [ ] **Step 3: Commit any final touch-ups**

```bash
git add -A && git commit -m "chore: Plan 1 foundation complete" || echo "nothing to commit"
```

---

## Done criteria (Plan 1)

- `pytest engine/` green (validation, scoring w/ skip-exclusion, gate, report, CLI, fixture).
- Security signals proven to locate the fixture's planted vulns.
- Engine end-to-end: expected security result → markdown report + gate exit code 1.
- Foundation files exist: `schema.json`, `discovery.md` (+archetype), `scoring.md`,
  `config-schema.md`, `plugin.json`.
- One working dimension skill + minimal orchestrator wired to the engine.

**Next:** Plan 2 (remaining 10 dimension skills) · Plan 3 (HTML dashboard, SARIF,
compliance-map generation, full config + menu).
