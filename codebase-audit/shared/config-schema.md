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

# Suppress specific findings (checklist_id@file)
suppress:
  - sec_weak_crypto@legacy/old_hash.py
```

Precedence: CLI flags > `.codebase-audit.yml` > defaults.
