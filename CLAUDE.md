# CLAUDE.md — codebase-audit

Context for continuing work on this repo. The deliverable is a **tool-agnostic Agent Skills
bundle** (installable with `npx skills add`, and still as a Claude Code plugin) that audits
any codebase across 11 ISO/IEC 25010 dimensions and emits Markdown, SARIF, and HTML.

## Workflow rule (from the repo owner — always follow)

For every change, no matter how small it looks:

1. **Brainstorm** — discuss options, trade-offs and open questions. No file changes.
2. **Spec** — write a short spec (goal, decisions, scope, out of scope). Wait for approval.
3. **Plan** — list the steps and files they touch. Wait for approval.
4. **Execute** — only after the plan is approved, and only on a work branch (never `main`
   or `dev` directly).

A question from the owner ("what is your suggestion?") is not approval to implement.

**Branch flow** — `work branch → dev → release/vX.Y.Z → main`; merging into `main` auto-tags
`vX.Y.Z` (full checklists: `RELEASING.md`).

| Branch | Use for | Created from | PR into |
|---|---|---|---|
| `feature/<name>` | new features | `dev` | `dev` |
| `fix/<name>` | bug fixes | `dev` (hotfix: `main`) | `dev` (hotfix: `main`) |
| `refactor/<name>` | restructuring without behaviour change | `dev` | `dev` |
| `chore/<name>` | maintenance: docs, dependencies, CI, tooling | `dev` | `dev` |
| `release/vX.Y.Z` | preparing a release (version bump, stabilisation) | `dev` | `main` |

Use short kebab-case names, e.g. `fix/fail-open-gate`, `chore/update-docs`. Squash is fine
into `dev`; `dev → release`, `release → main` and the `main → dev` back-merge are **merge
commits only**. Never create, move or delete `v*` tags by hand.

## Repo layout

```
codebase-audit/                         # plugin root (also what `npx skills` discovers via marketplace.json)
  .claude-plugin/plugin.json            # Claude Code manifest (author MUST be an object); version = release version
  skills/                               # SHIPPED: each folder is installed on its own
    audit-<dim>/SKILL.md                # 11 thin dimension skills
    audit-<dim>/references/             # GENERATED copies (its spec + examples, discovery, schema, scoring)
    codebase-audit/SKILL.md             # orchestrator
    codebase-audit/references/          # GENERATED copies (all 11 specs + examples, discovery, schema, scoring, config, compliance)
    codebase-audit/scripts/run_engine.py# engine entry point (works from any cwd)
    codebase-audit/scripts/engine/      # deterministic Python: validate/scoring/gate/report_md/sarif/html (+ generated schema.json)
    codebase-audit/scripts/requirements.txt
  shared/                               # SOURCE OF TRUTH (not shipped): detection/NN-*.md (+examples), discovery, scoring, schema, config-schema
    compliance-map.md                   # GENERATED from inline compliance_refs (do not hand-edit)
  tools/                                # dev-only: sync_skills.py (shared -> skills), compliance.py,
                                        #   bump_version.py, release_gate.py, versioning.py
  tests/                                # pytest: engine, fail-closed gate, packaging contract
  test-fixture/ + expected/             # planted-vuln fixtures + expected results
.claude-plugin/marketplace.json         # repo-root marketplace listing (source: ./codebase-audit)
.github/workflows/                     # ci.yml (tests, sync check, npx-skills install smoke),
                                        # release-gate.yml (PRs into main), release.yml (push to main -> tag + release)
RELEASING.md                            # release + hotfix checklists, merge rules, GitHub rulesets
README.md USAGE.md                      # user docs
docs/superpowers/specs/                 # the design spec (single source of design decisions; §13 = tool-agnostic)
docs/superpowers/plans/                 # the 4 implementation plans (Plan 1-4)
```

## Architecture (how it works)

1. Orchestrator (`/codebase-audit`) resolves `SKILL_DIR` (its own folder) and runs
   `references/discovery.md` once in the audited repo → `.codebase-audit/discovery.json`.
2. It selects dimensions (config / menu / `--all` / `--ci`), drops dim 10 when no IaC, and runs
   each dimension as a **parallel subagent where the agent supports it, sequentially otherwise**.
   Each writes one `AuditResult` to `.codebase-audit/results/<key>.json` (leaves `score: 0`).
3. Each dimension follows its `references/detection/NN-*.md` spec: **grep-first two-stage
   detection** (rg `signals` locate candidates → LLM confirms only the snippets).
4. The orchestrator runs `python3 <SKILL_DIR>/scripts/run_engine.py --results-dir … --expect …`.
   The **engine** (deterministic Python, never the LLM) validates, scores, gates, and renders.

## Non-obvious conventions (read before editing)

- **Edit `shared/`, never `skills/*/references/`**. Then run `python -m tools.sync_skills`.
  `tests/test_packaging.py` + CI (`--check`) fail on any drift. The copies exist because the
  Agent Skills standard / `npx skills` installs only skill folders — verified empirically:
  files outside a skill folder are not installed.
- **No tool-specific paths in SKILL.md**: no `${CLAUDE_PLUGIN_ROOT}`, no `shared/`, no `/tmp/`.
  Paths are relative to the skill folder (`references/…`, `scripts/…`). Enforced by tests.
- **Skills can't fan out in parallel** — only subagents can, and how is tool-specific. The
  orchestrator describes the task generically and falls back to sequential runs.
- **Fail-closed**: `--expect` lists selected dimensions; any missing/invalid result becomes an
  `error` placeholder → scored **ERROR** (excluded from the average, never a free 10) and fails
  the CI gate unless `gate.fail_on_error: false`.
- **Score vs gate** (`shared/scoring.md`): the 0–10 score is display-only. The CI gate uses
  **raw severity counts**. Fully-skipped dimension = **N/A**. Status enum is exactly
  `pass|fail|warning|skipped` (schema-enforced).
- **Discovery excludes installed-skill folders** (`.agents/`, `.claude/`, `.codex/`, …) — with
  project-level installs the audit's own engine sits inside the audited repo.
- **Versions**: `plugin.json` version == `engine.__version__` (test-enforced); the release
  workflow also requires the git tag to match. SARIF `driver.version` reads `__version__`.
- **Invocation**: only `codebase-audit` may be started by the agent on its own. The 11
  `audit-*` skills carry `disable-model-invocation: true` (top-level; read by Cursor and Claude
  Code) — the one field the official `agentskills validate` rejects, deliberately; tests allow
  exactly this extra field. Descriptions follow *what + "Use when" + "Not for"* (test-enforced).
- **Mode selection lives in the orchestrator SKILL.md** ("Choosing what to run": request >
  `.codebase-audit.yml` `mode`/`dimensions` > defaults; never show a menu nobody can answer).
  The engine only reads `gate`/`suppress`. Behaviour in real agents is checked by hand with
  `docs/testing/agent-invocation.md` (Cursor first).
- **Detection specs are intent-first**: `signals` are non-exhaustive candidate locators,
  `confirm` is the decision rule. Security core-vulns keep a High severity floor. Cross-refs
  push overlaps to owning dimensions (no double-counting).

## Common commands

```bash
cd codebase-audit
pip install -r requirements-dev.txt
python -m tools.sync_skills             # after editing shared/ (also regenerates compliance-map.md)
python -m tools.sync_skills --check     # verify copies
pytest tests -v                         # 78 tests
python -m tools.bump_version 1.2.0      # set the version everywhere (release branches only)
python -m tools.release_gate --head release/v1.2.0   # what the release-gate check runs
# manual engine run (any cwd):
python3 skills/codebase-audit/scripts/run_engine.py --results-dir R --expect security,api \
  --out report.md --formats html,md,sarif --total-lines 1000 [--ci]
# install smoke test into a scratch project:
npx -y skills@1.7.6 add /path/to/claude-codebase-audit -a codex -y
# what users run (latest / pinned):
npx skills add appuk45/claude-codebase-audit
npx skills add https://github.com/appuk45/claude-codebase-audit/tree/vX.Y.Z
```

## Status & roadmap

- **v1.0.0**: 11 dimension skills + orchestrator + engine, Claude Code plugin only. Merged to
  `main` via PRs #1–#4.
- **v1.1.0** (released 2026-11-11, PRs #5–#7): tool-agnostic Agent Skills layout, `npx skills`
  install, fail-closed gate for errored dimensions, CI, and the release flow
  (dev → release/vX.Y.Z → main, auto-tag).
- **v1.1.1** (hotfix): install docs. Unpinned `npx skills add appuk45/claude-codebase-audit`
  = latest release; pin with `…/claude-codebase-audit/tree/vX.Y.Z`. The short
  `owner/repo@vX.Y.Z` form installs nothing on `skills` < 1.8.1. `release.yml` now installs
  each published tag from GitHub to verify it.
- **Known gaps**: detection accuracy is unmeasured (no test runs an LLM against the fixture);
  the line-normalized display score barely moves on large repos; only Python + JS/TS specs;
  Windows needs Git Bash/WSL (discovery is POSIX shell).
- **Deferred to v2**: `audit-testing`, `audit-data-privacy`, `audit-accessibility`,
  `audit-fix`; per-dimension fixture expansion (JS/Dockerfile/.tf).

## When continuing

Start from `docs/superpowers/specs/` (design, esp. §5a, §9a, §13) and `docs/superpowers/plans/`.
To add a dimension: write `shared/detection/NN-*.md` (+ examples), clone a `skills/audit-*`
SKILL.md, add it to `tools/sync_skills.py` `DIMENSIONS`, `engine.DIMENSIONS`, and the
orchestrator table, then sync. Keep detection logic in the spec, math in the engine.
