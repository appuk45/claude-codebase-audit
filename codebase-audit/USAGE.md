# Using codebase-audit

## 1. Install

**Via marketplace:**
```
/plugin marketplace add appuk45/claude-codebase-audit
/plugin install codebase-audit
```

**From a local clone** (development / air-gapped):
```
git clone https://github.com/appuk45/claude-codebase-audit
/plugin marketplace add ./claude-codebase-audit
/plugin install codebase-audit
```

First run installs the Python deps (`jsonschema`, `PyYAML`) if they are missing.

## 2. Run your first audit

From the root of the repo you want to audit:
```
/codebase-audit --all
```
The orchestrator discovers the stack + archetype, runs each applicable dimension as a parallel
subagent, and writes `audit-report.html` (open it in a browser) and `audit-report.md`.

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
      # ... run `/codebase-audit --ci` via your Claude Code CI runner ...
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

## 7. Troubleshooting

- **"No module named engine"** — the orchestrator runs the engine from the plugin root; if you
  invoke it manually, `cd` into the plugin directory first.
- **Missing Python deps** — `pip install -r requirements.txt` inside the plugin directory.
- **A dimension shows all `skipped`** — it doesn't apply to this project archetype (e.g.
  Container & IaC with no Dockerfile). That's expected; it is excluded from the overall score.
