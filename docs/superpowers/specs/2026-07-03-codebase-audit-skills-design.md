# Codebase Audit — Multi-Skill Design

**Date:** 2026-07-03
**Status:** Approved (design phase)
**Source:** Refactor of the monolithic draft skill at `/home/appuk/Appu/codebase-audit/codebase-audit/`

---

## 1. Goal

Split the existing single monolithic `codebase-audit` skill into a suite of composable,
enterprise-ready skills. The suite must work for everything from a small side project
to an enterprise-grade application:

- Each audit **dimension** is its own standalone, invokable skill.
- An **orchestrator** skill composes all dimensions into a unified report.
- Enterprise integration: **SARIF output**, **CI gating (exit codes)**, **config file**,
  **compliance mapping**.
- Language coverage: **Python (Django/FastAPI/Flask) + JS/TS (Express/Fastify)** — matches
  the draft. Extensible later.

## 2. Key Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Decomposition axis | **By dimension** — 11 standalone dimension skills + 1 orchestrator | User wants each dimension usable alone; orchestrator composes. |
| Shared machinery | **Self-contained dimensions** for *detection*, but *cross-cutting* logic lives in shared bundled files | Standalone independence without 10× drift of scoring/schema/enterprise logic. |
| Enterprise features | SARIF + CI gating, config file, compliance mapping (**no** baseline/diff mode) | YAGNI on baseline; the other three are core enterprise needs. |
| Language coverage | Python + JS/TS only | Ship deep/accurate on 2 stacks; expand later. |
| Parallelism | **Agent/subagent tool**, not the Skill tool | Skill tool loads inline in the main thread → cannot fan out 10 concurrently. Subagents can. |
| CI gate metric | **Raw severity counts**, not the 0–10 score | Line-normalized score is gameable by adding code; counts are not. |
| Packaging | **Single plugin bundle** | All skills + `shared/` ship together. |

### 2.1 The "self-contained vs shared" boundary (load-bearing)

The user chose "self-contained dimensions." That means **detection logic** runs standalone
per skill. It does **NOT** mean duplicating cross-cutting logic. Concretely:

- **Self-contained (per dimension):** invoking discovery when run standalone, applying its
  own detection checklist, emitting its own JSON + markdown.
- **Shared (bundled files, consumed — never re-implemented):** the detection spec content,
  the scoring formula, the JSON schema, the compliance map, the SARIF field mapping, the
  config schema.

Shared items are **bundled reference files**, not runtime skill-to-skill dependencies. This
is what the user rejected ("dimension triggers discovery via a core *skill*") vs. what is
fine ("dimension reads a bundled spec *file*"). A dimension skill reading `shared/scoring.md`
is not a runtime dependency on another skill.

## 3. Architecture & Layout

Single plugin bundle. Three layers: **shared assets** (source of truth) · **11 thin
dimension skills** · **1 orchestrator**.

```
codebase-audit/                    # plugin root
  .claude-plugin/plugin.json
  shared/
    detection/                     # promoted from the draft's audits/
      01-performance.md  02-security.md  03-enterprise.md
      04-issues.md  05-architecture.md  06-dependencies.md
      07-i18n.md  08-api.md  09-resilience.md  10-container-iac.md
      11-observability.md          # NEW
      examples/                    # curated pos/neg snippets, loaded ON DEMAND only (5a.2)
        01-performance.md  ...  11-observability.md
    discovery.md                   # stack-detect commands + archetype classification (see 5a.1)
    scoring.md                     # ONE score formula + CI-gate rules
    schema.json                    # AuditResult JSON contract (validates every dim)
    compliance-map.md              # checklist_id -> OWASP/CIS/SOC2/PCI controls
    sarif-mapping.md               # finding -> SARIF 2.1.0 result fields
    config-schema.md               # .codebase-audit.yml spec
  skills/
    audit-performance/SKILL.md
    audit-security/SKILL.md
    audit-enterprise/SKILL.md
    audit-issues/SKILL.md
    audit-architecture/SKILL.md
    audit-dependencies/SKILL.md    # licensing/SBOM folded in here
    audit-i18n/SKILL.md
    audit-api/SKILL.md
    audit-resilience/SKILL.md
    audit-container-iac/SKILL.md
    audit-observability/SKILL.md   # NEW
    codebase-audit/                # orchestrator
      SKILL.md
      phases/
        html-generate.md          # from draft, + compliance column
        merge-and-gate.md         # NEW: merge, SARIF, CI gate
  test-fixture/                    # draft's bad_views.py etc, expanded
    expected/                      # per-dimension expected AuditResult JSON
```

**Rule:** dimension skills own *detection invocation only*. Everything cross-cutting
(scoring formula, schema, compliance, SARIF, config, HTML) lives in `shared/` and is
consumed by the orchestrator. A dimension skill reads `shared/scoring.md` and its own
`shared/detection/NN-*.md` — it never re-implements them.

## 4. Skill Roster

**12 skills total** — 11 dimension + 1 orchestrator.

| # | Skill | Trigger | ISO 25010 | Draft audit |
|---|---|---|---|---|
| 1 | audit-performance | `/audit-performance` | Performance Efficiency | 01 |
| 2 | audit-security | `/audit-security` | Security | 02 |
| 3 | audit-enterprise | `/audit-enterprise` | Reliability | 03 |
| 4 | audit-issues | `/audit-issues` | Maintainability | 04 |
| 5 | audit-architecture | `/audit-architecture` | Reliability | 05 |
| 6 | audit-dependencies | `/audit-dependencies` | Security | 06 (+ licensing/SBOM) |
| 7 | audit-i18n | `/audit-i18n` | Portability | 07 |
| 8 | audit-api | `/audit-api` | Compatibility | 08 |
| 9 | audit-resilience | `/audit-resilience` | Fault Tolerance | 09 |
| 10 | audit-container-iac | `/audit-container-iac` | Portability | 10 (auto-skip if no IaC) |
| 11 | audit-observability | `/audit-observability` | Operability | NEW |
| — | codebase-audit | `/codebase-audit` | orchestrator | SKILL.md + phases |

ISO characteristics are not unique per dimension (e.g. 3 and 5 both map to Reliability).
That is expected.

**Deferred to v2** (considered, not built now): audit-testing, audit-data-privacy,
audit-accessibility, audit-fix (remediation). Licensing/SBOM is folded into
audit-dependencies rather than a standalone skill.

## 5. Dimension Skill Contract

Every dimension skill has the same thin shape. Example — `audit-security`:

```
Trigger: /audit-security  [--json]
Input:   optional injected discovery_context (from orchestrator)

Steps:
  1. If discovery_context absent (standalone run) -> run shared/discovery.md, build it.
     If present (subagent run) -> use injected context, skip discovery.
        # This fixes the "discovery runs 10x" problem under orchestration.
  2. Filter checklist by discovery_context.archetypes -> non-applicable items = "skipped".
  3. TWO-STAGE DETECTION (token-bounded, see 5a.2):
       a. Mechanical scan: run each applicable item's `signals` (ripgrep/AST) + relevant
          external-tool output -> candidate file:line list. NO whole-repo LLM read.
       b. LLM confirm: read ONLY candidate snippets (+/- a few lines). Apply the item's
          confirm/reject rule; assign severity (with context modifiers). Consult
          shared/detection/examples/NN-*.md ONLY if a candidate is ambiguous.
  4. Score via shared/scoring.md formula.
  5. Emit AuditResult JSON (validates against shared/schema.json).
       - standalone (no --json): also print a terse markdown summary (findings + score).
       - --json or subagent invocation: JSON only, no prose.
```

Detection *content* lives in `shared/detection/NN-*.md`; the skill is the *runner*. The same
spec file drives the standalone skill AND the orchestrator subagent, so the two paths cannot
diverge. Adding a dimension = one new spec file + a ~15-line skill clone.

## 5a. Genericity & Project Adaptivity

The draft's detection is brittle — patterns hardcoded to specific frameworks
(e.g. "Django view without `@login_required`"). The suite must be **generic** (work on any
Python / JS-TS project) and **adaptive** (adjust to project type). Three mechanisms:

### 5a.1 Project archetype classification

Discovery classifies the repo into one or more archetypes:

```
web-api | frontend-spa | fullstack | cli-tool | library | data-ml | worker-service
```

Stored on `discovery_context.archetypes[]`. Classification uses entry points, deps, and
structure (e.g. presence of route/controller dirs -> web-api; `bin`/`__main__`/argparse ->
cli-tool; published package manifest with no server -> library; React/Vue/Svelte + build ->
frontend-spa; notebooks/pandas/torch -> data-ml).

### 5a.2 Per-item detection schema (intent-first)

Every checklist item in `shared/detection/NN-*.md` follows this schema. Detection is
**intent-first**; patterns are **hints, explicitly non-exhaustive**. The audit agent reasons
about whatever framework is actually present rather than matching a fixed rule.

```
id             stable key, e.g. perf_n_plus_one       (also the SARIF ruleId + compliance key)
label          short human label
intent         what this checks and WHY it matters     (framework-agnostic, 1 line)
applies_to     archetypes/stacks where relevant; else auto-status "skipped"
signals        compact ripgrep/AST patterns to LOCATE candidate file:line (NON-exhaustive)
criteria       confirm/reject rule for a candidate + when pass/fail/warning/skip (1-2 lines)
severity       base severity + context modifiers (see 5a.3)
remediation    concrete fix guidance (1 line)
compliance_refs OWASP/CWE/CIS/ISO refs where applicable (feeds compliance-map.md)
```

Items are kept **compact** (no inline prose examples) to bound per-subagent token cost.
Curated positive/negative code examples live in `shared/detection/examples/NN-*.md` and are
**loaded on demand only** (progressive disclosure) — the agent reads them only when a
candidate is genuinely ambiguous, so they cost zero tokens on the common path.

An item whose `applies_to` excludes all of the repo's archetypes is emitted as
`status: "skipped"` (not counted against the score).

### 5a.3 Context-aware severity

Base severity can be modified by project maturity/context, supplied via config:

```yaml
# .codebase-audit.yml
context:
  maturity: prototype | internal | production | enterprise   # default: production
```

Example: `sec_auth_failures` (no rate limit) = High at `enterprise`/`production`, Low at
`prototype`/`internal`. Modifiers are declared per-item in the detection spec and applied by
the audit agent. This keeps one checklist usable from mini projects to enterprise apps.

## 6. Orchestrator Flow (`codebase-audit`)

```
/codebase-audit  [--all] [--ci] [--config PATH] [--formats html,sarif,md]

Phase 0  Load config      Read .codebase-audit.yml if present; else defaults.
                          Resolves: selected dims, path ignores, gate thresholds, suppressions.
Phase 1  Discovery        Run shared/discovery.md ONCE -> discovery_context.
Phase 2  Menu             Skip if --all / --ci / config-driven (draft behavior).
Phase 3  Dispatch         N parallel subagents (Agent tool), each given:
                          discovery_context + one shared/detection/NN spec.
                          Each returns AuditResult JSON. (This is the parallel path.)
Phase 3b External tools   bandit / semgrep / trivy / npm audit / gitleaks / radon / eslint /
                          checkov merge (draft logic preserved).
Phase 4  Merge + validate Collect AuditResult[], validate each vs shared/schema.json.
                          Invalid -> recorded as error entry (draft behavior).
Phase 5  Enrich           Join findings -> compliance-map (OWASP/CIS/SOC2/PCI).
Phase 6  Outputs          Per --formats:
                            html  -> phases/html-generate.md (dashboard + compliance column)
                            sarif -> phases/merge-and-gate.md -> audit-report.sarif (2.1.0)
                            md    -> audit-report.md (CI logs / PR comment)
Phase 7  CI gate (--ci)   phases/merge-and-gate.md: count severities across ALL dims vs
                          thresholds. Suppressions applied before counting.
                          Threshold exceeded -> exit 1 (print which). Else exit 0.
```

- **Local mode** (default): interactive menu, HTML output.
- **CI mode** (`--ci`): non-interactive, SARIF + markdown, sets process exit code.
- **Config precedence:** CLI flags > `.codebase-audit.yml` > defaults.
- Dim 10 (container-iac) auto-skipped by the orchestrator when `discovery_context.has_iac == false`
  (draft rule). The standalone `audit-container-iac` skill still runs on demand.

## 7. Shared Assets (source of truth)

- **`schema.json`** — every dimension emits this exact shape:
  `{ audit, score, iso_characteristic, checklist[], findings[] }`. Findings carry
  `checklist_id, file, line, severity, title, detail, recommendation`. The orchestrator
  validates each subagent's JSON against this schema.
- **`scoring.md`** — the 0–10 line-normalized display score
  (`10 − (H×2.0 + M×0.8 + L×0.3)/lines×1000`, floored at 0). **Display only.** CI gating
  uses raw severity counts, defined here once.
- **`compliance-map.md`** — table keyed by `checklist_id`
  (e.g. `sec_injection -> OWASP A03:2021, CWE-89, PCI-DSS 6.5.1`). Joined to findings at
  report time. Zero per-skill work. Must include entries for the new
  `audit-observability` checklist_ids.
- **`sarif-mapping.md`** — how a finding becomes a SARIF 2.1.0 `result`:
  `ruleId = checklist_id`, `level` from severity, `region` from `file:line`,
  `partialFingerprints` for dedup.
- **`config-schema.md`** — `.codebase-audit.yml`: selected dimensions, path ignores,
  severity overrides, gate thresholds, suppressions.

## 8. Outputs

| Format | File | Purpose | Contents |
|---|---|---|---|
| HTML | `audit-report-YYYY-MM-DD.html` | human dashboard | Draft's self-contained Chart.js dashboard **+ new Compliance column** (finding -> OWASP/CIS/SOC2/PCI). Fully offline. |
| SARIF | `audit-report.sarif` | CI code-scanning | SARIF 2.1.0. One `run`, `tool.driver.rules[]` = checklist items, `results[]` = findings. Ingested by GitHub/GitLab. |
| Markdown | `audit-report.md` | CI log / PR comment | Score table per dim + severity totals + top findings. Diff-friendly. |

Default local = HTML. Default `--ci` = SARIF + markdown. `--formats` overrides.

## 9. Scoring & CI Gating

- **Display score** (unchanged from draft): radar/gauge only, labeled "indicative" in the
  report footer.
- **CI gate** (new, authoritative): raw counts across all dimensions vs config thresholds.

```yaml
# .codebase-audit.yml
gate:
  max_high: 0        # any High above this -> fail
  max_medium: 10
  max_low: null      # null = ignore
suppress:
  - sec_crypto@legacy/old_hash.py
```

Any threshold exceeded -> exit 1 and print which. All within -> exit 0. Suppressions are
removed before counting.

**Why counts, not score:** a line-normalized score lets a large repo dilute real High
findings past a score-based gate. Counts cannot be gamed by adding code.

## 9a. Build-Phase Contract Decisions

Resolved before writing shared assets (else they distort results or drift):

### 9a.1 How skips score

Archetype gating means a dimension (or item) can be fully non-applicable. Rules:

- **A fully-skipped dimension is excluded from the overall-score average and reported as
  `N/A`** — it does NOT contribute a free 10/10. (Zero findings on an inapplicable dimension
  must not inflate the headline number.)
- **Per-dimension `pass_rate` is computed over applicable items only** —
  `passed / (total − skipped)`. "2 pass, 8 skip" = 100%, not 20%.
- A dimension with applicable items but zero findings scores normally (up to 10).

### 9a.2 Compliance data — single source

`compliance_refs` inline in each `shared/detection/NN-*.md` item is the **source of truth**.
`shared/compliance-map.md` is **generated from** those inline refs (a build/derived artifact),
never hand-maintained in parallel. This preserves the "one source, no drift" principle.

### 9a.3 Canonical status enum

The one allowed set of checklist-item statuses is: **`pass` | `fail` | `warning` | `skipped`**.
- `schema.json` enforces this enum on every emitted item.
- All 11 detection specs already emit these values.
- `phases/html-generate.md` MUST map `skipped` (the draft template matched `"skip"` and fell
  through to a ⚠️ warning icon — fix it to render `skipped` as ⏭️ and exclude from pass/fail
  counts). Reconcile the enum across schema + specs + template when building.

### 9a.4 Signals are candidate-locators, validated empirically

Detection `signals` locate candidates; multi-line constructs (e.g. bare `except:` then `pass`
on the next line) must be found by matching the opening line and reading the body — never
assume the pattern is single-line. Validate signals against `test-fixture/` before wiring
skills (this caught a real miss in `issue_error_swallowing`).

## 10. Testing

- **`test-fixture/`** expanded from the draft: known-bad Python (Django) + JS/TS files, each
  planted vulnerability mapped to a specific `checklist_id`. Add a `Dockerfile` + a `.tf`
  file for dimension 10, and a logging-gap example for dimension 11.
- **`test-fixture/expected/`** — per-dimension expected AuditResult JSON (fixtures have known
  findings, so detection can be asserted).
- **Verification** (per skill, TDD): run a dimension skill against the fixture; assert its
  JSON matches expected checklist statuses + finding counts.
- **Orchestrator tests:** `--ci` on the fixture exits 1; the SARIF output validates against
  the SARIF 2.1.0 schema; the HTML output contains zero unexpanded `[placeholder]` tokens
  and zero unexpanded FOREACH/IF comment blocks.
- Scope guard: Python + JS/TS fixtures only (matches the language decision).

## 11. Migration From Draft

- `audits/NN-*.md` -> `shared/detection/NN-*.md` (content preserved, header tweaked to note
  it is a shared spec consumed by both a standalone skill and an orchestrator subagent).
- `phases/discovery.md` -> `shared/discovery.md`.
- `phases/html-generate.md` -> `skills/codebase-audit/phases/html-generate.md`
  (+ compliance column).
- Draft `SKILL.md` orchestration logic -> `skills/codebase-audit/SKILL.md`, extended with
  config load, compliance enrichment, SARIF/markdown output, CI gate.
- New: `shared/scoring.md`, `shared/schema.json`, `shared/compliance-map.md`,
  `shared/sarif-mapping.md`, `shared/config-schema.md`,
  `shared/detection/11-observability.md`, `phases/merge-and-gate.md`, 11 thin dimension
  `SKILL.md` files.

## 12. Out of Scope (v1)

- Baseline / git-diff incremental mode.
- Languages beyond Python + JS/TS.
- audit-testing, audit-data-privacy, audit-accessibility, audit-fix skills.
- Standalone licensing/SBOM skill (folded into audit-dependencies).
