# Using codebase-audit

## 1. Install

**Any agent, pinned release (recommended):**
```bash
npx skills add appuk45/claude-codebase-audit@v1.1.0
```
The installer detects your coding agents (Claude Code, Codex, Cursor, GitHub Copilot, Gemini
CLI, OpenCode, …) or asks which to target. Choose explicitly with `-a`, and use `-g` for a
user-wide install instead of a per-project one:
```bash
npx skills add appuk45/claude-codebase-audit@v1.1.0 -a codex -a cursor -g
```
Skills land in `.agents/skills/` (project) and are symlinked into each agent's own folder.
Commit `skills-lock.json` and run `npx skills check` in CI to catch unreviewed changes.
To upgrade, re-run `add` with the new tag; `npx skills remove` uninstalls.

**Claude Code plugin marketplace (Claude Code only):**
```
/plugin marketplace add appuk45/claude-codebase-audit
/plugin install codebase-audit
```

**From a local clone** (development / air-gapped):
```bash
git clone https://github.com/appuk45/claude-codebase-audit
npx skills add ./claude-codebase-audit
```

The engine needs Python 3.11+ with `jsonschema` and `PyYAML`; the orchestrator offers to
install them (from the skill's `scripts/requirements.txt`) on first run.

## 2. Run your first audit

From the root of the repo you want to audit:
```
/codebase-audit --all
```
The orchestrator discovers the stack + archetype, runs each applicable dimension (as parallel
subagents where your agent supports them, otherwise one after another), and writes `audit-report.html` (open it in a browser) and `audit-report.md`.

Run a single dimension standalone:
```
/audit-security
/audit-performance
```

## 3. Read the HTML dashboard

`audit-report.html` is fully self-contained (open it directly — no server needed). It shows:
- overall score and severity totals,
- a per-dimension score card (dimensions that don't apply show **N/A**, not a fake 10),
- per-dimension checklists (pass / fail / warning / skipped icons),
- a findings table per dimension with **file:line**, a **compliance** column
  (OWASP/CWE/CIS/ISO), and a recommendation.

## 4. Configure with `.codebase-audit.yml`

Place this file in the audited repo's root:
```yaml
dimensions: [security, performance, dependencies]   # omit for all applicable
context:
  maturity: production        # prototype | internal | production | enterprise
ignore:
  - "**/migrations/**"
  - "**/node_modules/**"
gate:
  max_high: 0                 # fail if any High finding
  max_medium: 10
  max_low: null               # null = ignore
  fail_on_error: true         # a dimension that did not run fails the gate (default)
suppress:
  - sec_weak_crypto@legacy/old_hash.py
```
`maturity` adjusts severities (e.g. a missing rate limit is High for `enterprise`, lower for
`prototype`). Core security issues keep a High floor regardless.

## 5. Wire into CI (SARIF code-scanning)

`--ci` writes SARIF and sets a non-zero exit code when the gate is breached. Example GitHub
Actions job that uploads findings to code-scanning:

```yaml
name: codebase-audit
on: [pull_request]
jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      # ... install the pinned skills, then run `/codebase-audit --ci` through your
      #     agent's headless mode (e.g. `claude -p`, `codex exec`) ...
      - name: Upload SARIF
        if: always()                       # upload even when the gate fails
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: audit-report.sarif
```
The gate exit code fails the check; the SARIF surfaces each finding inline on the PR.

## 6. Interpret the CI gate

The gate compares **raw severity counts** across all dimensions to `gate.*` thresholds
(`null` = ignore). It deliberately does NOT gate on the 0-10 score, which a large repo could
dilute. Suppressions (`checklist_id@file`) are removed before counting.

A selected dimension that produced no valid result (subagent crash, invalid JSON) is shown as
**ERROR** — never as a clean 10/10 — and fails the gate unless `gate.fail_on_error: false`.
Exit codes: `0` pass, `1` gate breach, `2` invalid input.

## 7. Troubleshooting

- **Missing Python deps** — `python3 -m pip install -r <skill-dir>/scripts/requirements.txt`,
  where `<skill-dir>` is the installed `codebase-audit` skill (e.g. `.agents/skills/codebase-audit`).
- **A dimension shows ERROR** — its result file in `.codebase-audit/results/` was missing or
  invalid. Re-run that dimension; the engine's stderr names the reason.
- **Working files** — runs write to `.codebase-audit/` in the audited repo; add it to `.gitignore`.
- **A dimension shows all `skipped`** — it doesn't apply to this project archetype (e.g.
  Container & IaC with no Dockerfile). That's expected; it is excluded from the overall score.
