# codebase-audit

An enterprise-grade, multi-dimension **codebase audit** for AI coding agents — Claude Code,
Codex, Cursor, GitHub Copilot and any other client that supports the open
[Agent Skills](https://github.com/agentskills/agentskills) standard. It statically
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

- An Agent Skills client: Claude Code, Codex, Cursor, GitHub Copilot, Gemini CLI, OpenCode, …
- A POSIX shell (bash/zsh; Git Bash or WSL on Windows).
- Python 3.11+ with `jsonschema` and `PyYAML` (for the scoring/report engine). The
  orchestrator offers to install them on first run if missing.
- Node.js 22.20+ only for the `npx skills` installer.
- Optional external tools (auto-used if present): `ripgrep`, `bandit`, `semgrep`, `radon`,
  `eslint`, `npm audit`, `pip-audit`, `osv-scanner`, `gitleaks`, `trivy`, `checkov`, `hadolint`.

## Install (any agent)

Pinned to a release (recommended — reproducible, auditable):

```bash
npx skills add appuk45/claude-codebase-audit@v1.1.0
```

The [`skills`](https://github.com/vercel-labs/skills) CLI detects the coding agents you have
installed (or asks which ones) and installs all 12 skills into a shared `.agents/skills/`
folder, symlinked for each agent. Pick agents explicitly with `-a`, install user-wide with `-g`:

```bash
npx skills add appuk45/claude-codebase-audit@v1.1.0 -a claude-code -a codex -a cursor -a github-copilot
```

Install all 12 skills — the orchestrator dispatches dimensions itself, but standalone
`/audit-*` commands need their own skill. `skills-lock.json` records a hash per skill; commit
it and use `npx skills check` in CI to detect drift.

**Claude Code plugin (alternative):** `/plugin marketplace add appuk45/claude-codebase-audit`
then `/plugin install codebase-audit`.

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

Every skill folder is self-contained (the Agent Skills standard installs folders, nothing
else), so the shared sources are copied into each skill by a sync tool:

```
codebase-audit/
  skills/audit-*/SKILL.md              thin LLM skills: discover -> grep signals -> confirm -> JSON
  skills/audit-*/references/           generated copies: its detection spec, discovery, schema
  skills/codebase-audit/SKILL.md       orchestrator: select -> parallel subagents (or sequential) -> engine
  skills/codebase-audit/references/    generated copies: all 11 specs, discovery, schema, config, compliance
  skills/codebase-audit/scripts/       deterministic Python engine (run_engine.py): validate/score/gate/md/sarif/html
  shared/                              SOURCE OF TRUTH for specs, discovery, scoring, schema, config
  tools/                               dev-only: sync_skills.py, compliance.py (not shipped)
  tests/                               pytest (engine, fail-closed gate, packaging contract)
```

Dimensions run as parallel subagents where the agent supports them (Claude Code, Codex,
Cursor, Copilot) and sequentially otherwise. A dimension that fails to produce a result is
reported as **ERROR** and fails the CI gate by default (`gate.fail_on_error`).

## Development

```bash
cd codebase-audit
pip install -r requirements-dev.txt
python -m tools.sync_skills          # after editing anything in shared/
python -m tools.sync_skills --check  # CI: copies must match shared/
pytest tests -v
```

## Releasing (pinned versions)

1. Bump the version in `codebase-audit/.claude-plugin/plugin.json` and
   `codebase-audit/skills/codebase-audit/scripts/engine/__init__.py` (a test enforces they match).
2. Merge to `main`, then tag: `git tag v1.1.0 && git push origin v1.1.0`.
3. The `release` workflow checks the tag matches both versions, runs the tests, and publishes
   a GitHub release. Users pin with `npx skills add appuk45/claude-codebase-audit@v1.1.0`.

Scoring/gate rules: `shared/scoring.md`. Result contract: `shared/schema.json`.
