# `.codebase-audit.yml` — configuration

```yaml
# How the orchestrator runs (default: interactive)
#   interactive  show the dimension menu when nothing else selects dimensions
#   all          no menu: run all applicable (or the listed) dimensions, HTML + markdown
#   ci           no menu: SARIF + markdown + gate exit code
mode: interactive

# Which dimensions to run (default: all applicable)
dimensions: [security, performance]      # omit for all

# Project maturity — adjusts context-severity modifiers
context:
  maturity: production                   # prototype | internal | production | enterprise

# Paths to ignore during detection
ignore:
  - "**/migrations/**"
  - "**/node_modules/**"

# CI gate thresholds (raw severity counts; null = ignore)
gate:
  max_high: 0
  max_medium: 10
  max_low: null
  fail_on_error: true                     # a dimension that did not run fails the gate

# Suppress specific findings (checklist_id@file)
suppress:
  - sec_weak_crypto@legacy/old_hash.py
```

Precedence: the user's request (words or flags such as `--all`, `--ci`) > `.codebase-audit.yml`
> defaults. `mode` and `dimensions` are read by the orchestrator skill; `gate` and `suppress`
are read by the engine (which has no gate flags). Whatever the mode, a run that cannot ask the
user (headless, CI) never shows the menu.

`fail_on_error` (default `true`): a selected dimension that produced no valid result
(subagent crash, invalid JSON, never written) is reported as **ERROR** and fails the gate.
Set it to `false` only if you accept a partial audit passing CI.
