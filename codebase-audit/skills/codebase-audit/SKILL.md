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
| 1 | performance | audit-performance | ${CLAUDE_PLUGIN_ROOT}/shared/detection/01-performance.md |
| 2 | security | audit-security | ${CLAUDE_PLUGIN_ROOT}/shared/detection/02-security.md |
| 3 | enterprise | audit-enterprise | ${CLAUDE_PLUGIN_ROOT}/shared/detection/03-enterprise.md |
| 4 | issues | audit-issues | ${CLAUDE_PLUGIN_ROOT}/shared/detection/04-issues.md |
| 5 | architecture | audit-architecture | ${CLAUDE_PLUGIN_ROOT}/shared/detection/05-architecture.md |
| 6 | dependencies | audit-dependencies | ${CLAUDE_PLUGIN_ROOT}/shared/detection/06-dependencies.md |
| 7 | i18n | audit-i18n | ${CLAUDE_PLUGIN_ROOT}/shared/detection/07-i18n.md |
| 8 | api | audit-api | ${CLAUDE_PLUGIN_ROOT}/shared/detection/08-api.md |
| 9 | resilience | audit-resilience | ${CLAUDE_PLUGIN_ROOT}/shared/detection/09-resilience.md |
| 10 | container_iac | audit-container-iac | ${CLAUDE_PLUGIN_ROOT}/shared/detection/10-container-iac.md |
| 11 | observability | audit-observability | ${CLAUDE_PLUGIN_ROOT}/shared/detection/11-observability.md |

## Steps

1. **Config**: if `--config` given or `.codebase-audit.yml` exists, load it (see
   `${CLAUDE_PLUGIN_ROOT}/shared/config-schema.md`). Read `dimensions` (selection), `context.maturity`, `ignore`,
   `gate`, `suppress`.
2. **Discovery**: run `${CLAUDE_PLUGIN_ROOT}/shared/discovery.md` ONCE. Build `discovery_context` (including
   `archetypes`, `has_iac`, `total_lines`). Print:
   `Discovered: [languages] | archetypes: [...] | files: [n] | IaC: [yes/no]`.
   Run the discovery commands in the audited repo (the current working directory) BEFORE any cd into the plugin root.
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
   The engine validates, scores (N/A for fully-skipped dims, excluded from the average),
   gates on raw severity counts, and writes `audit-report.md`.
7. **Report**: print the engine's stdout and the path to `audit-report.md`. In `--ci` mode,
   propagate the engine's exit code (non-zero = gate breach). Local mode writes audit-report.html; --ci writes audit-report.sarif for code-scanning upload.

Do not compute scores or gate logic yourself — the engine owns that (`${CLAUDE_PLUGIN_ROOT}/shared/scoring.md`).
Dimensions are independent; dispatch them concurrently for speed.
