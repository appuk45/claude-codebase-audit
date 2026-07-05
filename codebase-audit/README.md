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
