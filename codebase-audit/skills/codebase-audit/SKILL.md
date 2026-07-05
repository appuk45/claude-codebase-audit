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
   # local (default): rich HTML dashboard
   python -m engine.cli --results /tmp/codebase-audit-results.json \
     --out audit-report.md --formats html,md \
     --html-out audit-report.html --total-lines <total_lines> [--config <path>]

   # CI (--ci): SARIF + markdown + gate exit code
   python -m engine.cli --results /tmp/codebase-audit-results.json \
     --out audit-report.md --formats sarif,md \
     --sarif-out audit-report.sarif --total-lines <total_lines> [--config <path>] --ci
   ```
   The engine validates, scores (N/A for fully-skipped dims, excluded from the average),
   gates on raw severity counts, and writes `audit-report.md`.
7. **Report**: print the engine's stdout and the path to `audit-report.md`. In `--ci` mode,
   propagate the engine's exit code (non-zero = gate breach). Local mode writes audit-report.html; --ci writes audit-report.sarif for code-scanning upload.

Do not compute scores or gate logic yourself — the engine owns that (`shared/scoring.md`).
Dimensions are independent; dispatch them concurrently for speed.
