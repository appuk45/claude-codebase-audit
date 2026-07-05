# CLAUDE.md — codebase-audit

Context for continuing work on this repo. The deliverable is a **Claude Code plugin** that
audits any codebase across 11 ISO/IEC 25010 dimensions and emits Markdown, SARIF, and HTML.

## Repo layout

```
codebase-audit/                 # the plugin (plugin root = this dir)
  .claude-plugin/plugin.json    # manifest (author MUST be an object, not a string)
  skills/
    audit-<dim>/SKILL.md        # 11 thin dimension skills
    codebase-audit/SKILL.md     # orchestrator
  shared/
    detection/NN-*.md           # the 11 detection specs (checklists + rg signals + criteria)
    detection/examples/NN-*.md  # on-demand FAIL/PASS snippets (progressive disclosure)
    discovery.md                # stack + archetype classification
    scoring.md schema.json      # scoring/gate rules + AuditResult contract
    config-schema.md            # .codebase-audit.yml spec
    compliance-map.md           # GENERATED from inline compliance_refs (do not hand-edit)
  engine/                       # deterministic Python: validate/scoring/gate/report_md/sarif/html/compliance/cli
  engine/tests/                 # pytest (33 tests)
  engine/assets/chart.umd.min.js# vendored Chart.js (offline HTML)
  test-fixture/ + expected/     # planted-vuln fixtures + expected results
  README.md USAGE.md            # user docs
.claude-plugin/marketplace.json # repo-root marketplace listing (source: ./codebase-audit)
docs/superpowers/specs/         # the design spec (single source of design decisions)
docs/superpowers/plans/         # the 4 implementation plans (Plan 1-4)
```

## Architecture (how it works)

1. Orchestrator (`/codebase-audit`) runs `shared/discovery.md` once → `discovery_context`
   (languages, archetypes, has_iac, total_lines, maturity).
2. It selects dimensions (config / menu / `--all` / `--ci`), drops dim 10 when no IaC, and
   dispatches each selected dimension as a **parallel Agent subagent**.
3. Each dimension skill reads its `shared/detection/NN-*.md` spec, runs **grep-first
   two-stage detection** (rg `signals` locate candidates → LLM confirms only the snippets),
   and emits an `AuditResult` JSON object (leaves `score: 0`).
4. The orchestrator collects the JSON array and calls `python -m engine.cli`. The **engine**
   (deterministic Python, never the LLM) validates against `schema.json`, computes scores,
   the CI gate, and renders Markdown / SARIF / HTML.

## Non-obvious conventions (read before editing)

- **Skills can't fan out in parallel** — only Agent/subagents can. Parallelism lives in the
  orchestrator, not the Skill tool. Standalone dimension skills and the subagent path share
  the same `shared/detection/NN` spec, so detection logic never drifts.
- **`${CLAUDE_PLUGIN_ROOT}`**: every bundled-file reference in a skill uses it (the plugin is
  installed elsewhere than the audited repo). The orchestrator captures `AUDIT_CWD=$(pwd)`,
  `cd`s to the plugin root to import `engine`, and writes reports back to `$AUDIT_CWD`.
- **Score vs gate** (`shared/scoring.md`, engine): the 0–10 score is display-only. The CI
  gate uses **raw severity counts** (gameable score is never gated). A fully-skipped
  dimension scores **N/A** and is excluded from the average; pass-rate counts applicable
  items only. Status enum is exactly `pass|fail|warning|skipped` (schema-enforced).
- **Compliance map is generated** from the specs' inline `compliance_refs`
  (`python -m engine.compliance`). Specs are the source of truth — never hand-edit
  `compliance-map.md`.
- **Detection specs are intent-first**: `signals` are rg candidate-locators (non-exhaustive),
  `confirm` is the decision rule. Reason about the actual framework; security core-vulns keep
  a High severity floor regardless of maturity. Cross-refs push overlaps to owning dimensions
  (no double-counting) — see the "Cross-references" section in each spec.
- Design rationale for all of the above: `docs/superpowers/specs/2026-07-03-codebase-audit-skills-design.md`
  (esp. §5a adaptivity, §9a build contracts).

## Common commands

```bash
cd codebase-audit
pytest engine/ -v                       # 33 tests
python -m engine.compliance             # regenerate shared/compliance-map.md from specs
# manual engine run (from plugin dir so `engine` imports):
python -m engine.cli --results results.json --out report.md \
  --formats html,md --html-out report.html --total-lines 1000
```

Run the audit itself with the installed plugin: `/codebase-audit --all` (or `--ci`), or a
single dimension e.g. `/audit-security`.

## Status & roadmap

- **v1 complete**: 11 dimension skills + orchestrator + engine (md/sarif/html/compliance/gate),
  33 tests green, installable, documented. Built across Plans 1–4 (see `docs/superpowers/plans/`).
- **Branch**: all work is on `codebase-audit-skills`. **`main` has only the initial commit** —
  merge/PR the branch to `main` so the marketplace (which tracks the default branch) resolves
  the plugin cleanly.
- **Deferred to v2** (considered, not built): `audit-testing`, `audit-data-privacy`,
  `audit-accessibility`, `audit-fix` (remediation). Also: per-dimension `test-fixture`
  expansion (JS/Dockerfile/.tf), and publishing to a shared marketplace.
- Language coverage is Python + JS/TS by design; other stacks would need new detection specs.

## When continuing

Start from `docs/superpowers/specs/` (design) and `docs/superpowers/plans/` (the 4 plans).
To add a dimension: write `shared/detection/NN-*.md` (+ examples), clone a `skills/audit-*`
SKILL.md, add its row to the orchestrator table, and (if it needs new checks) update the
schema/tests. Keep detection logic in the spec, math in the engine.
