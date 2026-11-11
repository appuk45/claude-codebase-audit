# `.codebase-audit.yml` — configuration

```yaml
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

Precedence: `.codebase-audit.yml` > defaults (the engine has no gate flags).

`fail_on_error` (default `true`): a selected dimension that produced no valid result
(subagent crash, invalid JSON, never written) is reported as **ERROR** and fails the gate.
Set it to `false` only if you accept a partial audit passing CI.
