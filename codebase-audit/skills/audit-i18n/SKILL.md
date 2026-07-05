---
name: audit-i18n
description: Internationalization dimension audit — emits AuditResult JSON; runs standalone or as an orchestrator subagent.
---

# /audit-i18n

Audit the current working directory for the Internationalization dimension.

## Inputs
- Optional `discovery_context` (JSON) injected by the orchestrator.
- Flags: `--json` (emit JSON only, no markdown summary).

## Steps

1. **Discovery**: if `discovery_context` was NOT injected, run `shared/discovery.md` and
   build it. If injected, use it as-is (do not re-run discovery).
2. **Filter**: read `shared/detection/07-i18n.md`. Drop any checklist item whose
   `applies_to` shares no archetype with `discovery_context.archetypes` → emit it with
   `status: "skipped"`.
3. **Detect (two-stage, spec §5a.2 / §9a.4)**:
   a. For each applicable item, run its `signals` (ripgrep) to get candidate `file:line`.
      Prefer external-tool output if available. Do NOT read the whole repo.
   b. Read only candidate snippets; apply each item's `confirm` rule. Assign severity
      honoring any severity floors. Consult `shared/detection/examples/07-i18n.md` only
      when a candidate is ambiguous.
4. **Emit**: produce one `AuditResult` JSON object conforming to `shared/schema.json` with
   `audit: "i18n"`, `iso_characteristic: "Portability"`, the checklist (with
   statuses), and findings. Leave `score` as `0` — the engine computes it.
   - With `--json` or as a subagent: output ONLY the JSON.
   - Standalone: also print a short markdown summary (counts + top findings).

Return only valid JSON when invoked as a subagent.
