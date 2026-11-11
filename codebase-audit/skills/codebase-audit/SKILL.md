---
name: codebase-audit
description: Orchestrates the 11-dimension codebase audit (ISO/IEC 25010, OWASP 2025) — discovery, dimension selection, parallel or sequential dimension runs, deterministic scoring and CI gate, and Markdown/SARIF/HTML reports. Use when asked to audit a codebase or run /codebase-audit.
compatibility: Requires a POSIX shell (bash/zsh; Git Bash or WSL on Windows) and Python 3.11+ with jsonschema and PyYAML (scripts/requirements.txt). ripgrep recommended. Works in any Agent Skills client (Claude Code, Codex, Cursor, GitHub Copilot, ...).
---

# /codebase-audit

Run a multi-dimension static audit of the current working directory.

```
/codebase-audit            # show the dimension menu
/codebase-audit --all      # run all applicable dimensions, no menu
/codebase-audit --ci       # non-interactive: all applicable dims, gate + exit code
/codebase-audit --config PATH
```

## Paths

- `SKILL_DIR` = the absolute path of the directory containing this SKILL.md. Every
  `references/...` and `scripts/...` path below is relative to `SKILL_DIR`. Resolve it
  once and use absolute paths when handing files to subagents.
- `AUDIT_CWD` = the repository being audited (the current working directory). All
  detection commands run here, and all outputs are written here.
- Working files go in `AUDIT_CWD/.codebase-audit/` (add it to `.gitignore`).

## Dimensions

| # | audit key | detection spec (relative to `SKILL_DIR`) |
|---|---|---|
| 1 | performance | `references/detection/01-performance.md` |
| 2 | security | `references/detection/02-security.md` |
| 3 | enterprise | `references/detection/03-enterprise.md` |
| 4 | issues | `references/detection/04-issues.md` |
| 5 | architecture | `references/detection/05-architecture.md` |
| 6 | dependencies | `references/detection/06-dependencies.md` |
| 7 | i18n | `references/detection/07-i18n.md` |
| 8 | api | `references/detection/08-api.md` |
| 9 | resilience | `references/detection/09-resilience.md` |
| 10 | container_iac | `references/detection/10-container-iac.md` |
| 11 | observability | `references/detection/11-observability.md` |

Each spec has on-demand examples at `references/detection/examples/<same file name>`.

## Steps

1. **Config**: if `--config` is given or `.codebase-audit.yml` exists in `AUDIT_CWD`, load it
   (format: `references/config-schema.md`). Read `dimensions`, `context.maturity`, `ignore`,
   `gate`, `suppress`.
2. **Prepare**: `rm -rf .codebase-audit/results && mkdir -p .codebase-audit/results`
   (in `AUDIT_CWD`). Stale result files must never leak into a new run.
3. **Discovery**: follow `references/discovery.md` ONCE, in `AUDIT_CWD`. Build
   `discovery_context` (including `archetypes`, `has_iac`, `total_lines`) and write it to
   `.codebase-audit/discovery.json`. Print:
   `Discovered: [languages] | archetypes: [...] | files: [n] | IaC: [yes/no]`.
4. **Select dimensions**:
   - If config `dimensions` is set → use it.
   - Else if `--all`/`--ci` → all 11.
   - Else → present the menu (numbers 1–11 from the table) and read the user's choice
     (comma-separated numbers or `all`).
   - **Always drop dimension 10 (container_iac) when `discovery_context.has_iac == false`**,
     and note: `Dimension 10 (Container & IaC) skipped — no Dockerfile/Terraform/K8s found`.
   Print: `Running: [selected audit keys]`. Remember this list as `EXPECTED`.
5. **Run each selected dimension** with this task (fill in the placeholders):

   > Audit the repository at `AUDIT_CWD` for the `<audit key>` dimension.
   > discovery_context: `<JSON>`. Maturity: `<maturity>`. Ignore paths: `<globs>`.
   > Read the detection spec `<SKILL_DIR>/references/detection/<NN-name>.md` and follow its
   > "How to use this spec" section: skip non-applicable items as `skipped`, run each item's
   > `signals` to locate candidates, read only candidate snippets, apply `confirm`, assign
   > severity. Consult `<SKILL_DIR>/references/detection/examples/<NN-name>.md` only for
   > ambiguous candidates. Do not read the whole repository.
   > Write exactly one AuditResult JSON object conforming to
   > `<SKILL_DIR>/references/schema.json` (audit = `<audit key>`, score = 0) to
   > `AUDIT_CWD/.codebase-audit/results/<audit key>.json`. Reply with one line:
   > `<audit key>: <n> findings`.

   - **If your environment can run subagents** (e.g. Claude Code's Agent/Task tool, Codex
     subagents, Cursor or GitHub Copilot custom agents/subagents), dispatch one subagent per
     dimension **in parallel** — do not wait for one before starting the next.
   - **Otherwise run them one at a time** in this session. Finish and write each result file
     before starting the next dimension, and do not carry one dimension's snippets into the
     next — the result file is the only state that matters.
   - Print `✓ <audit key>: <n> findings` as each completes. If a dimension fails, do NOT
     write a placeholder: the engine records any missing or invalid result itself.
6. **Engine** (deterministic — never compute scores or the gate yourself). Run in `AUDIT_CWD`.
   Use `python3`, or `python` where `python3` does not exist.
   ```bash
   # Runtime deps (jsonschema + PyYAML). In interactive mode ask the user before installing.
   python3 -c "import jsonschema, yaml" 2>/dev/null || \
     python3 -m pip install -q -r "<SKILL_DIR>/scripts/requirements.txt"

   # Local (default): HTML dashboard + markdown
   python3 "<SKILL_DIR>/scripts/run_engine.py" \
     --results-dir .codebase-audit/results --expect <EXPECTED, comma-separated> \
     --discovery .codebase-audit/discovery.json \
     --out audit-report.md --formats html,md --html-out audit-report.html \
     --total-lines <total_lines> [--config .codebase-audit.yml]

   # CI (--ci): SARIF + markdown + gate exit code
   python3 "<SKILL_DIR>/scripts/run_engine.py" \
     --results-dir .codebase-audit/results --expect <EXPECTED, comma-separated> \
     --out audit-report.md --formats sarif,md --sarif-out audit-report.sarif \
     --total-lines <total_lines> [--config .codebase-audit.yml] --ci
   ```
   `--expect` makes the run fail-closed: a selected dimension with no valid result file is
   reported as ERROR (never as a clean 10/10) and, by default, fails the CI gate
   (`gate.fail_on_error`, see `references/config-schema.md`). Always pass `--total-lines`.
7. **Report**: print the engine's stdout/stderr and the report paths. In `--ci` mode,
   propagate the engine's exit code (0 = pass, 1 = gate breach, 2 = invalid input).

Scoring and gate rules: `references/scoring.md`. Compliance mapping:
`references/compliance-map.md`.
