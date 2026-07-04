---
name: codebase-audit
description: Orchestrates the multi-dimension codebase audit — discovery, parallel dimension subagents, deterministic scoring/gate, report output.
---

# /codebase-audit

Run a multi-dimension static audit of the current working directory.

```
/codebase-audit [--ci] [--config PATH]
```

Plan-1 scope: runs the Security dimension end-to-end. (Additional dimensions and HTML/SARIF
outputs are added by later plans.)

## Steps

1. **Config**: if `--config` given or `.codebase-audit.yml` exists, load it (see
   `shared/config-schema.md`). Otherwise use defaults.
2. **Discovery**: run `shared/discovery.md` ONCE. Build `discovery_context` (including
   `archetypes` and `total_lines`). Print:
   `Discovered: [languages] | archetypes: [...] | files: [n]`.
3. **Dispatch**: launch the `audit-security` work as a subagent (Agent tool), passing
   `discovery_context` and instructing it to read `shared/detection/02-security.md` and emit
   AuditResult JSON only. (This is the parallel path; with more dimensions, dispatch them
   concurrently.)
4. **Collect**: gather the AuditResult JSON object(s) into a JSON array; write it to
   `/tmp/codebase-audit-results.json`.
5. **Engine**: run
   ```bash
   python -m engine.cli \
     --results /tmp/codebase-audit-results.json \
     --out audit-report.md \
     --total-lines <discovery_context.total_lines> \
     [--config <path>] [--ci]
   ```
   from the plugin directory (so `engine` imports resolve). The engine validates, scores
   (with skip-exclusion), gates, and writes `audit-report.md`. In `--ci` mode its exit code
   is the gate result.
6. **Report**: print the engine's stdout and the path to `audit-report.md`. In `--ci` mode,
   propagate the engine exit code.

Do not compute scores or gate logic yourself — the engine owns that (`shared/scoring.md`).
