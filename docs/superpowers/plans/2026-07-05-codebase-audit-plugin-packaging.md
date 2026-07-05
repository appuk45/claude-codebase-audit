# Codebase Audit — Plan 4: Plugin Packaging + Docs

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the completed audit suite a real, installable Claude Code plugin — fix path portability so skills work from any audited repo, add a runtime dependency story, refresh metadata, add a marketplace manifest, and ship a README + usage/how-to guide.

**Architecture:** No engine logic changes. Skills are edited so every reference to a bundled file uses `${CLAUDE_PLUGIN_ROOT}/...` (the env var Claude Code sets to the plugin's install directory), and the orchestrator runs the engine from `${CLAUDE_PLUGIN_ROOT}` while writing reports to the audited repo's working directory. Packaging files (`requirements.txt`, refreshed `plugin.json`, repo-root `.claude-plugin/marketplace.json`) and docs (`README.md`, `USAGE.md`) are added.

**Tech Stack:** Claude Code plugin conventions (`.claude-plugin/`, `${CLAUDE_PLUGIN_ROOT}`), Python engine (unchanged), Markdown docs.

---

## File Structure

- Create: `codebase-audit/requirements.txt` — runtime deps (jsonschema, PyYAML).
- Modify: `codebase-audit/.claude-plugin/plugin.json` — refresh description, bump to 1.0.0, add metadata.
- Create: `.claude-plugin/marketplace.json` (repo root) — single-plugin marketplace listing.
- Modify: all 11 `codebase-audit/skills/audit-*/SKILL.md` + `codebase-audit/skills/codebase-audit/SKILL.md` — `${CLAUDE_PLUGIN_ROOT}` paths; orchestrator engine-invocation block + dep preflight + absolute report output.
- Create: `codebase-audit/README.md` — overview, install, usage, outputs, architecture.
- Create: `codebase-audit/USAGE.md` — step-by-step how-to incl. CI/SARIF.

No tests change; verification is static (path coverage, JSON validity) plus the unchanged engine suite must stay green.

---

## Task 1: Packaging files

**Files:**
- Create: `codebase-audit/requirements.txt`
- Modify: `codebase-audit/.claude-plugin/plugin.json`
- Create: `.claude-plugin/marketplace.json` (repo root)

- [ ] **Step 1: Runtime requirements**

`codebase-audit/requirements.txt`:
```
jsonschema>=4.0
PyYAML>=6.0
```

- [ ] **Step 2: Refresh plugin.json**

Overwrite `codebase-audit/.claude-plugin/plugin.json`:
```json
{
  "name": "codebase-audit",
  "version": "1.0.0",
  "description": "Enterprise codebase audit across 11 ISO/IEC 25010 dimensions — security (OWASP 2025), performance, architecture, dependencies/supply-chain, resilience, observability and more. Grep-first, archetype-adaptive detection with a deterministic scoring/gate engine; outputs Markdown, SARIF 2.1.0 (CI code-scanning), and a self-contained HTML dashboard.",
  "author": "Appu K",
  "license": "MIT",
  "keywords": ["audit", "security", "owasp", "sarif", "iso25010", "code-quality", "ci", "static-analysis"]
}
```

- [ ] **Step 3: Marketplace manifest (repo root)**

Create `.claude-plugin/marketplace.json` at the REPO ROOT (`/home/appuk/Appu/claude-codebase-audit/.claude-plugin/marketplace.json`):
```json
{
  "name": "appuk-codebase-audit",
  "owner": { "name": "Appu K" },
  "plugins": [
    {
      "name": "codebase-audit",
      "source": "./codebase-audit",
      "description": "11-dimension enterprise codebase audit (ISO 25010, OWASP 2025) with SARIF + HTML outputs and a CI gate."
    }
  ]
}
```

- [ ] **Step 4: Validate JSON**

Run:
```bash
cd /home/appuk/Appu/claude-codebase-audit
python -c "import json; json.load(open('codebase-audit/.claude-plugin/plugin.json')); json.load(open('.claude-plugin/marketplace.json')); print('json ok')"
```
Expected: `json ok`.

- [ ] **Step 5: Commit**

```bash
git add codebase-audit/requirements.txt codebase-audit/.claude-plugin/plugin.json .claude-plugin/marketplace.json
git commit -m "chore: plugin packaging — runtime deps, refreshed manifest, marketplace"
```

---

## Task 2: Path portability (`${CLAUDE_PLUGIN_ROOT}`)

**Files:** all 11 `codebase-audit/skills/audit-*/SKILL.md` + `codebase-audit/skills/codebase-audit/SKILL.md`.

The problem: skills reference `shared/...` and run `python -m engine.cli` assuming the cwd is
the plugin dir — but when installed, the plugin lives elsewhere and the audited repo is the
cwd. Fix: prefix bundled-file paths with `${CLAUDE_PLUGIN_ROOT}/`, run the engine from the
plugin root, and write reports to the audited repo.

- [ ] **Step 1: Prefix bundled-file references in the 11 dimension skills**

For EACH file matching `codebase-audit/skills/audit-*/SKILL.md`, replace every occurrence of
`shared/` with `${CLAUDE_PLUGIN_ROOT}/shared/`. Do it with sed (idempotent — none are
prefixed yet):
```bash
cd /home/appuk/Appu/claude-codebase-audit/codebase-audit
for f in skills/audit-*/SKILL.md; do
  sed -i 's#\bshared/#${CLAUDE_PLUGIN_ROOT}/shared/#g' "$f"
done
```
Then verify no bare `shared/` remains and the prefixed form is present:
```bash
rg -n '[^/{]shared/detection' skills/audit-*/SKILL.md && echo "BARE REF FOUND" || echo "all prefixed"
rg -c '\$\{CLAUDE_PLUGIN_ROOT\}/shared/' skills/audit-*/SKILL.md | head
```
Expected: `all prefixed`, and each skill shows a non-zero count.

- [ ] **Step 2: Fix the orchestrator paths + engine invocation**

Edit `codebase-audit/skills/codebase-audit/SKILL.md`:

(a) In the dimension table and Steps, prefix `shared/` refs the same way:
```bash
cd /home/appuk/Appu/claude-codebase-audit/codebase-audit
sed -i 's#\bshared/#${CLAUDE_PLUGIN_ROOT}/shared/#g' skills/codebase-audit/SKILL.md
```

(b) Replace the entire Step 6 engine block (the two ```bash command blocks added in Plan 3)
with this single block that (i) ensures deps, (ii) captures the audited repo cwd, (iii) runs
the engine from the plugin root, (iv) writes reports back to the audited repo:
```bash
   # Ensure runtime deps once (jsonschema + PyYAML)
   python -c "import jsonschema, yaml" 2>/dev/null || \
     pip install -q -r "${CLAUDE_PLUGIN_ROOT}/requirements.txt"

   AUDIT_CWD="$(pwd)"           # the repo being audited
   cd "${CLAUDE_PLUGIN_ROOT}"   # so the `engine` package imports resolve

   # Local (default): HTML dashboard + markdown, written into the audited repo
   python -m engine.cli --results /tmp/codebase-audit-results.json \
     --out "$AUDIT_CWD/audit-report.md" --formats html,md \
     --html-out "$AUDIT_CWD/audit-report.html" \
     --total-lines <total_lines> [--config "$AUDIT_CWD/.codebase-audit.yml"]

   # CI (--ci): SARIF + markdown + gate exit code
   python -m engine.cli --results /tmp/codebase-audit-results.json \
     --out "$AUDIT_CWD/audit-report.md" --formats sarif,md \
     --sarif-out "$AUDIT_CWD/audit-report.sarif" \
     --total-lines <total_lines> [--config "$AUDIT_CWD/.codebase-audit.yml"] --ci
```

(c) Ensure Step 2 (Discovery) still runs its detection commands in the audited repo — add this
clarifying sentence to Step 2: `Run the discovery commands in the audited repo (the current
working directory) BEFORE any cd into the plugin root.`

- [ ] **Step 3: Verify orchestrator**

Run:
```bash
cd /home/appuk/Appu/claude-codebase-audit/codebase-audit
rg -q 'AUDIT_CWD="\$\(pwd\)"' skills/codebase-audit/SKILL.md && echo "cwd capture OK"
rg -q 'cd "\$\{CLAUDE_PLUGIN_ROOT\}"' skills/codebase-audit/SKILL.md && echo "cd plugin OK"
rg -q 'pip install -q -r "\$\{CLAUDE_PLUGIN_ROOT\}/requirements.txt"' skills/codebase-audit/SKILL.md && echo "dep preflight OK"
rg -n '[^/{]shared/detection' skills/codebase-audit/SKILL.md && echo "BARE REF FOUND" || echo "all prefixed"
```
Expected: `cwd capture OK`, `cd plugin OK`, `dep preflight OK`, `all prefixed`.

- [ ] **Step 4: Engine suite unaffected**

Run: `cd codebase-audit && pytest engine/ -q | tail -1`
Expected: 33 passed (no engine files changed).

- [ ] **Step 5: Commit**

```bash
git add codebase-audit/skills
git commit -m "fix: use \${CLAUDE_PLUGIN_ROOT} paths + run engine from plugin root, report to audited repo"
```

---

## Task 3: README + USAGE docs

**Files:**
- Create: `codebase-audit/README.md`
- Create: `codebase-audit/USAGE.md`

- [ ] **Step 1: Write README.md**

`codebase-audit/README.md`:
```markdown
# codebase-audit

An enterprise-grade, multi-dimension **codebase audit** plugin for Claude Code. It statically
audits a repository across **11 ISO/IEC 25010 dimensions**, adapts to the project type, and
produces a Markdown report, **SARIF 2.1.0** for CI code-scanning, and a self-contained **HTML
dashboard**.

## Dimensions

| # | Skill | Focus | ISO 25010 |
|---|---|---|---|
| 1 | `/audit-performance` | N+1, blocking I/O, pagination, caching | Performance Efficiency |
| 2 | `/audit-security` | OWASP Top 10:2025, injection, authz, secrets | Security |
| 3 | `/audit-enterprise` | 12-Factor, config, health, graceful shutdown | Reliability |
| 4 | `/audit-issues` | complexity, dead code, duplication, smells | Maintainability |
| 5 | `/audit-architecture` | coupling, layering, cycles, scalability | Reliability |
| 6 | `/audit-dependencies` | CVEs, lockfiles, licenses, SBOM, supply chain | Security |
| 7 | `/audit-i18n` | encoding, timezone, localization readiness | Portability |
| 8 | `/audit-api` | versioning, status codes, idempotency, errors | Compatibility |
| 9 | `/audit-resilience` | timeouts, retries, circuit breakers, DLQ | Fault Tolerance |
| 10 | `/audit-container-iac` | Dockerfile, K8s, Terraform (CIS) | Portability |
| 11 | `/audit-observability` | structured logs, PII, metrics, tracing (A09) | Operability |
| — | `/codebase-audit` | orchestrates all applicable dimensions | — |

## Highlights

- **Archetype-adaptive**: classifies the repo (web-api, frontend-spa, cli-tool, library,
  data-ml, worker-service, fullstack) and skips non-applicable checks.
- **Grep-first, token-bounded**: locates candidates with ripgrep, then confirms only the
  snippets — no whole-repo reads.
- **Deterministic engine**: a small tested Python package computes scores, the CI gate, SARIF,
  compliance mapping, and HTML — the LLM never does the math.
- **Compliance mapping**: findings map to OWASP / CWE / CIS / ISO controls
  (`shared/compliance-map.md`, generated from the specs).
- **CI gate**: fails the build on raw severity thresholds (not the gameable score).

## Requirements

- Claude Code with plugin support.
- Python 3.11+ with `jsonschema` and `PyYAML` (`pip install -r requirements.txt`). The
  orchestrator installs these automatically on first run if missing.
- Optional external tools (auto-used if present): `ripgrep`, `bandit`, `semgrep`, `radon`,
  `eslint`, `npm audit`, `pip-audit`, `osv-scanner`, `gitleaks`, `trivy`, `checkov`, `hadolint`.

## Install

Add this repository as a plugin marketplace, then install:

```
/plugin marketplace add appuk45/claude-codebase-audit
/plugin install codebase-audit
```

Or run locally from a clone (see USAGE.md).

## Usage

```
/codebase-audit            # menu — pick dimensions to run
/codebase-audit --all      # all applicable dimensions
/codebase-audit --ci       # non-interactive: SARIF + markdown + gate exit code
/audit-security            # run a single dimension standalone
```

See **USAGE.md** for a full walkthrough, config, and CI integration.

## Outputs

- `audit-report.md` — diff-friendly summary (scores, findings) for PRs/CI logs.
- `audit-report.html` — interactive self-contained dashboard (local default).
- `audit-report.sarif` — SARIF 2.1.0 for GitHub/GitLab code-scanning (`--ci`).

## Configuration

A `.codebase-audit.yml` in the audited repo selects dimensions, sets the CI gate, maturity
context, ignores, and suppressions. See `shared/config-schema.md`.

## Architecture

```
skills/audit-*/SKILL.md      thin LLM skills: discover -> grep signals -> confirm -> JSON
skills/codebase-audit/       orchestrator: select -> dispatch subagents -> engine
shared/detection/NN-*.md     the detection specs (checklists, signals, criteria)
shared/*.md / schema.json    discovery, scoring rules, config + result contract
engine/                      deterministic Python: validate/score/gate/md/sarif/html/compliance
```

## Development

```
pip install -r requirements-dev.txt
pytest engine/ -v
```

Scoring/gate rules: `shared/scoring.md`. Result contract: `shared/schema.json`.
```

- [ ] **Step 2: Write USAGE.md**

`codebase-audit/USAGE.md`:
```markdown
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
- per-dimension checklists (✅ pass · ❌ fail · ⚠️ warning · ⏭️ skipped),
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
(`null` = ignore). It deliberately does NOT gate on the 0–10 score, which a large repo could
dilute. Suppressions (`checklist_id@file`) are removed before counting.

## 7. Troubleshooting

- **"No module named engine"** — the orchestrator runs the engine from the plugin root; if you
  invoke it manually, `cd` into the plugin directory first.
- **Missing Python deps** — `pip install -r requirements.txt` inside the plugin directory.
- **A dimension shows all `skipped`** — it doesn't apply to this project archetype (e.g.
  Container & IaC with no Dockerfile). That's expected; it is excluded from the overall score.
```

- [ ] **Step 3: Commit**

```bash
git add codebase-audit/README.md codebase-audit/USAGE.md
git commit -m "docs: README + usage/how-to guide"
```

---

## Task 4: Final verification

- [ ] **Step 1: Engine suite green**

Run: `cd codebase-audit && pytest engine/ -q | tail -1`
Expected: 33 passed.

- [ ] **Step 2: Path portability complete**

Run:
```bash
cd /home/appuk/Appu/claude-codebase-audit/codebase-audit
echo "bare shared/detection refs (expect none):"
rg -n '[^/{]shared/detection' skills/ || echo "none"
echo "CLAUDE_PLUGIN_ROOT usage across skills (expect 12 files):"
rg -l 'CLAUDE_PLUGIN_ROOT' skills/ | wc -l
```
Expected: `none`, and `12`.

- [ ] **Step 3: Packaging + docs present and valid**

Run:
```bash
cd /home/appuk/Appu/claude-codebase-audit
python -c "import json; json.load(open('codebase-audit/.claude-plugin/plugin.json')); json.load(open('.claude-plugin/marketplace.json')); print('json ok')"
for f in codebase-audit/requirements.txt codebase-audit/README.md codebase-audit/USAGE.md; do
  test -f "$f" || echo "MISSING $f"
done
echo "checked"
```
Expected: `json ok`, only `checked` (no MISSING).

- [ ] **Step 4: Commit any touch-ups**

```bash
git add -A && git commit -m "chore: Plan 4 complete — installable plugin + docs" || echo "nothing to commit"
```

---

## Done criteria (Plan 4)

- `${CLAUDE_PLUGIN_ROOT}` used for every bundled-file reference in all 12 skills; no bare
  `shared/` refs remain.
- Orchestrator installs deps if missing, runs the engine from the plugin root, and writes
  reports into the audited repo (absolute paths).
- `requirements.txt`, refreshed `plugin.json` (v1.0.0), and repo-root `marketplace.json` exist
  and are valid JSON.
- `README.md` + `USAGE.md` cover install, usage, config, outputs, CI/SARIF, troubleshooting.
- Engine suite still green (33).

**After Plan 4:** the plugin is installable and documented. Optional v2: deferred skills
(testing, data-privacy, accessibility, remediation/fix), per-dimension fixture expansion,
publishing to a shared marketplace.
```
