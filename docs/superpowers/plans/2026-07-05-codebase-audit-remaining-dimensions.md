# Codebase Audit — Plan 2: Remaining Dimensions + Multi-Dim Orchestrator

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the remaining 10 dimension skills and upgrade the orchestrator to discover applicable dimensions, present a menu, dispatch them all as parallel subagents, and feed every result through the existing engine — so `/codebase-audit` audits all 11 dimensions with correct archetype/IaC skipping and N/A score-exclusion.

**Architecture:** Each dimension skill is a thin clone of the existing `skills/audit-security/SKILL.md`, differing only in name, description, ISO characteristic, `audit` key, and which `shared/detection/NN-*.md` spec it reads. The orchestrator (`skills/codebase-audit/SKILL.md`) is rewritten to select dimensions (config or menu), dispatch the selected dimension subagents in parallel, gate dimension 10 on `has_iac`, collect all AuditResult JSON, and call the unchanged engine. The Python engine already handles multi-dimension scoring, skip-exclusion, gating, and reporting (Plan 1) — no engine changes except one added multi-dim end-to-end test.

**Tech Stack:** Same as Plan 1 — Python engine (unchanged logic), Claude Code plugin skills (markdown), pytest.

---

## File Structure

- Create: `codebase-audit/skills/audit-performance/SKILL.md`
- Create: `codebase-audit/skills/audit-enterprise/SKILL.md`
- Create: `codebase-audit/skills/audit-issues/SKILL.md`
- Create: `codebase-audit/skills/audit-architecture/SKILL.md`
- Create: `codebase-audit/skills/audit-dependencies/SKILL.md`
- Create: `codebase-audit/skills/audit-i18n/SKILL.md`
- Create: `codebase-audit/skills/audit-api/SKILL.md`
- Create: `codebase-audit/skills/audit-resilience/SKILL.md`
- Create: `codebase-audit/skills/audit-container-iac/SKILL.md`
- Create: `codebase-audit/skills/audit-observability/SKILL.md`
- Modify: `codebase-audit/skills/codebase-audit/SKILL.md` (multi-dimension orchestrator)
- Create: `codebase-audit/test-fixture/expected/multi_dim_results.json` (synthetic multi-dim input incl. a fully-skipped dim)
- Create: `codebase-audit/engine/tests/test_cli_multidim.py` (end-to-end multi-dim run)

`skills/audit-security/SKILL.md` is the canonical template — do not modify it.

---

## Task 1: Generate the 10 dimension skills

**Files:** the 10 `skills/audit-<name>/SKILL.md` files listed above.

Each file is the security skill with five substitutions. The canonical template is
`skills/audit-security/SKILL.md`; its exact body is reproduced below with `<PLACEHOLDERS>`.

- [ ] **Step 1: Read the template**

Read `codebase-audit/skills/audit-security/SKILL.md` so you match its structure exactly.

- [ ] **Step 2: For each row in the table, write one SKILL.md**

Template (substitute the 5 placeholders per row; keep everything else identical to the
security skill, including the two-stage detection steps and the "Return only valid JSON when
invoked as a subagent." line):

````markdown
---
name: <SKILL_NAME>
description: <DESCRIPTION>
---

# /<SKILL_NAME>

Audit the current working directory for the <DIMENSION_TITLE> dimension.

## Inputs
- Optional `discovery_context` (JSON) injected by the orchestrator.
- Flags: `--json` (emit JSON only, no markdown summary).

## Steps

1. **Discovery**: if `discovery_context` was NOT injected, run `shared/discovery.md` and
   build it. If injected, use it as-is (do not re-run discovery).
2. **Filter**: read `shared/detection/<SPEC_FILE>`. Drop any checklist item whose
   `applies_to` shares no archetype with `discovery_context.archetypes` → emit it with
   `status: "skipped"`.
3. **Detect (two-stage, spec §5a.2 / §9a.4)**:
   a. For each applicable item, run its `signals` (ripgrep) to get candidate `file:line`.
      Prefer external-tool output if available. Do NOT read the whole repo.
   b. Read only candidate snippets; apply each item's `confirm` rule. Assign severity
      honoring any severity floors. Consult `shared/detection/examples/<SPEC_FILE>` only
      when a candidate is ambiguous.
4. **Emit**: produce one `AuditResult` JSON object conforming to `shared/schema.json` with
   `audit: "<AUDIT_KEY>"`, `iso_characteristic: "<ISO_CHARACTERISTIC>"`, the checklist (with
   statuses), and findings. Leave `score` as `0` — the engine computes it.
   - With `--json` or as a subagent: output ONLY the JSON.
   - Standalone: also print a short markdown summary (counts + top findings).

Return only valid JSON when invoked as a subagent.
````

Substitution table (one file per row):

| file path | SKILL_NAME | DIMENSION_TITLE | SPEC_FILE | AUDIT_KEY | ISO_CHARACTERISTIC | DESCRIPTION |
|---|---|---|---|---|---|---|
| skills/audit-performance/SKILL.md | audit-performance | Performance | 01-performance.md | performance | Performance Efficiency | Performance dimension audit (ISO 25010 Performance Efficiency) — emits AuditResult JSON; runs standalone or as an orchestrator subagent. |
| skills/audit-enterprise/SKILL.md | audit-enterprise | Enterprise Readiness | 03-enterprise.md | enterprise | Reliability | Enterprise-readiness dimension audit (12-Factor / production readiness) — emits AuditResult JSON; runs standalone or as an orchestrator subagent. |
| skills/audit-issues/SKILL.md | audit-issues | Issue Detection | 04-issues.md | issues | Maintainability | Maintainability/issue-detection dimension audit — emits AuditResult JSON; runs standalone or as an orchestrator subagent. |
| skills/audit-architecture/SKILL.md | audit-architecture | Architecture & Scalability | 05-architecture.md | architecture | Reliability | Architecture & scalability dimension audit — emits AuditResult JSON; runs standalone or as an orchestrator subagent. |
| skills/audit-dependencies/SKILL.md | audit-dependencies | Dependencies & Supply Chain | 06-dependencies.md | dependencies | Security | Dependencies & supply-chain dimension audit (OWASP A03:2025 / SCVS) — emits AuditResult JSON; runs standalone or as an orchestrator subagent. |
| skills/audit-i18n/SKILL.md | audit-i18n | Internationalization | 07-i18n.md | i18n | Portability | Internationalization dimension audit — emits AuditResult JSON; runs standalone or as an orchestrator subagent. |
| skills/audit-api/SKILL.md | audit-api | API Design Quality | 08-api.md | api | Compatibility | API design quality dimension audit (REST/GraphQL/gRPC) — emits AuditResult JSON; runs standalone or as an orchestrator subagent. |
| skills/audit-resilience/SKILL.md | audit-resilience | Resilience & Fault Tolerance | 09-resilience.md | resilience | Fault Tolerance | Resilience & fault-tolerance dimension audit — emits AuditResult JSON; runs standalone or as an orchestrator subagent. |
| skills/audit-container-iac/SKILL.md | audit-container-iac | Container & IaC Security | 10-container-iac.md | container_iac | Portability | Container & IaC security dimension audit (CIS Docker/K8s/Terraform) — emits AuditResult JSON; runs standalone or as an orchestrator subagent. |
| skills/audit-observability/SKILL.md | audit-observability | Observability | 11-observability.md | observability | Operability | Observability dimension audit (OWASP A09:2025) — emits AuditResult JSON; runs standalone or as an orchestrator subagent. |

Note: `AUDIT_KEY` must match the `audit` field used in each detection spec's return schema
(e.g. dimension 10 uses `container_iac`, matching `shared/detection/10-container-iac.md`).

- [ ] **Step 3: Verify all 10 exist with correct spec references and audit keys**

Run:
```bash
cd codebase-audit
for d in performance enterprise issues architecture dependencies i18n api resilience container-iac observability; do
  test -f "skills/audit-$d/SKILL.md" || echo "MISSING skills/audit-$d/SKILL.md"
done
echo "--- audit keys present ---"
rg -n "audit: \"(performance|enterprise|issues|architecture|dependencies|i18n|api|resilience|container_iac|observability)\"" skills/*/SKILL.md | wc -l
echo "--- each references its detection spec ---"
for n in 01-performance 03-enterprise 04-issues 05-architecture 06-dependencies 07-i18n 08-api 09-resilience 10-container-iac 11-observability; do
  rg -l "shared/detection/$n.md" skills/ >/dev/null || echo "NO REF to $n"
done
```
Expected: no `MISSING`, the audit-keys count is `10`, and no `NO REF` lines.

- [ ] **Step 4: Confirm every referenced detection spec + examples file exists**

Run:
```bash
cd codebase-audit
for n in 01-performance 03-enterprise 04-issues 05-architecture 06-dependencies 07-i18n 08-api 09-resilience 10-container-iac 11-observability; do
  test -f "shared/detection/$n.md" || echo "SPEC MISSING $n"
  test -f "shared/detection/examples/$n.md" || echo "EXAMPLES MISSING $n"
done
echo "checked"
```
Expected: only `checked` (no MISSING lines).

- [ ] **Step 5: Commit**

```bash
git add codebase-audit/skills/audit-performance codebase-audit/skills/audit-enterprise \
  codebase-audit/skills/audit-issues codebase-audit/skills/audit-architecture \
  codebase-audit/skills/audit-dependencies codebase-audit/skills/audit-i18n \
  codebase-audit/skills/audit-api codebase-audit/skills/audit-resilience \
  codebase-audit/skills/audit-container-iac codebase-audit/skills/audit-observability
git commit -m "feat: add the remaining 10 dimension skills"
```

---

## Task 2: Multi-dimension orchestrator

**Files:**
- Modify: `codebase-audit/skills/codebase-audit/SKILL.md` (replace entire file)

- [ ] **Step 1: Replace the orchestrator with the multi-dimension version**

Write `codebase-audit/skills/codebase-audit/SKILL.md` with exactly this content (the body
contains nested ``` fences — preserve them verbatim):

````markdown
---
name: codebase-audit
description: Orchestrates the 11-dimension codebase audit — discovery, dimension selection, parallel dimension subagents, deterministic scoring/gate, report output.
---

# /codebase-audit

Run a multi-dimension static audit of the current working directory.

```
/codebase-audit            # show the dimension menu
/codebase-audit --all      # run all applicable dimensions, no menu
/codebase-audit --ci       # non-interactive: all applicable dims, gate + exit code
/codebase-audit --config PATH
```

## Dimensions

| # | audit key | skill | detection spec |
|---|---|---|---|
| 1 | performance | audit-performance | shared/detection/01-performance.md |
| 2 | security | audit-security | shared/detection/02-security.md |
| 3 | enterprise | audit-enterprise | shared/detection/03-enterprise.md |
| 4 | issues | audit-issues | shared/detection/04-issues.md |
| 5 | architecture | audit-architecture | shared/detection/05-architecture.md |
| 6 | dependencies | audit-dependencies | shared/detection/06-dependencies.md |
| 7 | i18n | audit-i18n | shared/detection/07-i18n.md |
| 8 | api | audit-api | shared/detection/08-api.md |
| 9 | resilience | audit-resilience | shared/detection/09-resilience.md |
| 10 | container_iac | audit-container-iac | shared/detection/10-container-iac.md |
| 11 | observability | audit-observability | shared/detection/11-observability.md |

## Steps

1. **Config**: if `--config` given or `.codebase-audit.yml` exists, load it (see
   `shared/config-schema.md`). Read `dimensions` (selection), `context.maturity`, `ignore`,
   `gate`, `suppress`.
2. **Discovery**: run `shared/discovery.md` ONCE. Build `discovery_context` (including
   `archetypes`, `has_iac`, `total_lines`). Print:
   `Discovered: [languages] | archetypes: [...] | files: [n] | IaC: [yes/no]`.
3. **Select dimensions**:
   - If config `dimensions` is set → use it.
   - Else if `--all`/`--ci` → all 11.
   - Else → present the menu (numbers 1–11 from the table above) and read the user's choice
     (comma-separated numbers or `all`).
   - **Always drop dimension 10 (container_iac) when `discovery_context.has_iac == false`**,
     and note: `Dimension 10 (Container & IaC) skipped — no Dockerfile/Terraform/K8s found`.
   Print: `Running: [selected audit keys]`.
4. **Dispatch (parallel)**: for each selected dimension, launch its skill as a subagent
   (Agent tool) IN PARALLEL — do not wait for one before starting the next. Pass each
   subagent the `discovery_context` and instruct it to read its detection spec (from the
   table) and emit ONLY its AuditResult JSON. Print progress as each returns:
   `✓ [audit key]: [n] findings`.
5. **Collect**: assemble all returned AuditResult objects into a JSON array; write it to
   `/tmp/codebase-audit-results.json`. If a subagent failed or returned invalid JSON, record
   a placeholder object for it:
   `{ "audit": "<key>", "score": null, "iso_characteristic": "<iso>", "checklist": [],
      "findings": [], "error": "subagent failed" }`.
6. **Engine**: run from the plugin directory (so `engine` imports resolve):
   ```bash
   python -m engine.cli \
     --results /tmp/codebase-audit-results.json \
     --out audit-report.md \
     --total-lines <discovery_context.total_lines> \
     [--config <path>] [--ci]
   ```
   The engine validates, scores (N/A for fully-skipped dims, excluded from the average),
   gates on raw severity counts, and writes `audit-report.md`.
7. **Report**: print the engine's stdout and the path to `audit-report.md`. In `--ci` mode,
   propagate the engine's exit code (non-zero = gate breach).

Do not compute scores or gate logic yourself — the engine owns that (`shared/scoring.md`).
Dimensions are independent; dispatch them concurrently for speed.
````

- [ ] **Step 2: Verify the orchestrator references all 11 skills + the engine**

Run:
```bash
cd codebase-audit
rg -c "audit-observability|audit-container-iac|audit-performance" skills/codebase-audit/SKILL.md
rg -q "python -m engine.cli" skills/codebase-audit/SKILL.md && echo "engine ref OK"
rg -q "has_iac == false" skills/codebase-audit/SKILL.md && echo "iac gate OK"
```
Expected: a non-zero count, `engine ref OK`, and `iac gate OK`.

- [ ] **Step 3: Commit**

```bash
git add codebase-audit/skills/codebase-audit/SKILL.md
git commit -m "feat: multi-dimension orchestrator (menu, parallel dispatch, IaC gating)"
```

---

## Task 3: Multi-dimension engine end-to-end test

**Files:**
- Create: `codebase-audit/test-fixture/expected/multi_dim_results.json`
- Test: `codebase-audit/engine/tests/test_cli_multidim.py`

Proves the whole pipeline on multiple dimensions including a fully-skipped one (N/A excluded
from the average) — the case Plan 1's single-dimension run did not cover.

- [ ] **Step 1: Write the synthetic multi-dimension input**

`codebase-audit/test-fixture/expected/multi_dim_results.json`:
```json
[
  {
    "audit": "security", "score": 0, "iso_characteristic": "Security",
    "archetypes_applied": ["web-api"],
    "checklist": [
      {"id": "sec_injection", "label": "No injection", "status": "fail", "affected_count": 1}
    ],
    "findings": [
      {"checklist_id": "sec_injection", "file": "a.py", "line": 5, "severity": "High",
       "title": "SQL injection", "recommendation": "parameterize"}
    ]
  },
  {
    "audit": "performance", "score": 0, "iso_characteristic": "Performance Efficiency",
    "archetypes_applied": ["web-api"],
    "checklist": [
      {"id": "perf_pagination", "label": "List endpoints paginated", "status": "warning",
       "affected_count": 1}
    ],
    "findings": [
      {"checklist_id": "perf_pagination", "file": "a.py", "line": 3, "severity": "Medium",
       "title": "Unpaginated list endpoint", "recommendation": "add pagination"}
    ]
  },
  {
    "audit": "i18n", "score": null, "iso_characteristic": "Portability",
    "archetypes_applied": ["web-api"],
    "checklist": [
      {"id": "i18n_hardcoded_strings", "label": "Externalized strings", "status": "skipped",
       "affected_count": 0},
      {"id": "i18n_rtl", "label": "RTL support", "status": "skipped", "affected_count": 0}
    ],
    "findings": []
  }
]
```

- [ ] **Step 2: Write the failing test**

`codebase-audit/engine/tests/test_cli_multidim.py`:
```python
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
    # One High finding (security) breaches max_high=0 -> exit 1
    assert proc.returncode == 1
    assert "High" in proc.stdout
    report = out.read_text()
    # i18n is fully skipped -> shown as N/A, not 10/10
    assert "N/A" in report
    # security scored (1 High on 1000 lines -> 8.0), performance scored (1 Medium -> ~9.2)
    # overall = average of the two applicable dims only (i18n excluded)
    assert "security" in report and "performance" in report and "i18n" in report

def test_multidim_overall_excludes_skipped(tmp_path):
    # Directly assert the overall math via the engine functions
    sys.path.insert(0, str(ROOT))
    from engine.scoring import score_dimension, overall_score
    results = json.loads((ROOT / "test-fixture" / "expected" / "multi_dim_results.json").read_text())
    scores = [score_dimension(r, total_lines=1000) for r in results]
    # security: 10 - 2.0/1000*1000 = 8.0 ; performance: 10 - 0.8/1000*1000 = 9.2 ; i18n: None
    assert scores == [8.0, 9.2, None]
    assert overall_score(scores) == 8.6   # (8.0 + 9.2)/2, i18n excluded
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd codebase-audit && pytest engine/tests/test_cli_multidim.py -v`
Expected: FAIL — the fixture file `multi_dim_results.json` does not exist yet (if you did
Step 1 first, instead confirm it PASSES; if any assertion is wrong, STOP and report — do not
weaken the assertion).

- [ ] **Step 4: Ensure the fixture exists, then run to pass**

Run: `cd codebase-audit && pytest engine/tests/test_cli_multidim.py -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Run the whole engine suite**

Run: `cd codebase-audit && pytest engine/ -v`
Expected: PASS (Plan 1's 21 tests + these 2 = 23).

- [ ] **Step 6: Commit**

```bash
git add codebase-audit/test-fixture/expected/multi_dim_results.json \
  codebase-audit/engine/tests/test_cli_multidim.py
git commit -m "test: multi-dimension engine e2e (N/A exclusion + gate)"
```

---

## Task 4: Final verification

- [ ] **Step 1: Full engine suite green**

Run: `cd codebase-audit && pytest engine/ -v`
Expected: 23 passed.

- [ ] **Step 2: All 11 dimension skills present + orchestrator lists all**

Run:
```bash
cd codebase-audit
ls skills/ | grep -c '^audit-'          # expect 11 (10 new + audit-security)
rg -c "shared/detection/" skills/codebase-audit/SKILL.md   # orchestrator table references specs
```
Expected: `11`, and a non-zero reference count.

- [ ] **Step 3: No unexpanded placeholders in the new skills**

Run:
```bash
cd codebase-audit
rg -n "<SKILL_NAME>|<SPEC_FILE>|<AUDIT_KEY>|<ISO_CHARACTERISTIC>|<DESCRIPTION>|<DIMENSION_TITLE>" skills/ || echo "clean"
```
Expected: `clean`.

- [ ] **Step 4: Commit any final touch-ups**

```bash
git add -A && git commit -m "chore: Plan 2 complete — 11 dimensions wired" || echo "nothing to commit"
```

---

## Done criteria (Plan 2)

- All 11 dimension skills exist (`skills/audit-*`), each referencing its own detection spec +
  correct `audit` key + ISO characteristic; no unexpanded placeholders.
- Orchestrator selects dimensions (config/menu/`--all`/`--ci`), gates dimension 10 on
  `has_iac`, dispatches selected dimensions in parallel, and calls the engine.
- `pytest engine/` green (23), including a multi-dimension run proving N/A dims are excluded
  from the overall average and the gate still fires on a High finding.

**Next:** Plan 3 — HTML dashboard (`phases/html-generate.md` with compliance column + N/A
rendering), SARIF 2.1.0 output, `compliance-map.md` generated from inline `compliance_refs`,
full config/menu polish.
