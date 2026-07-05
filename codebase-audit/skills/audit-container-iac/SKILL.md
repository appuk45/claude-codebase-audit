---
name: audit-container-iac
description: Container & IaC security dimension audit (CIS Docker/K8s/Terraform) — emits AuditResult JSON; runs standalone or as an orchestrator subagent.
---

# /audit-container-iac

Audit the current working directory for the Container & IaC Security dimension.

## Inputs
- Optional `discovery_context` (JSON) injected by the orchestrator.
- Flags: `--json` (emit JSON only, no markdown summary).

## Steps

1. **Discovery**: if `discovery_context` was NOT injected, run `${CLAUDE_PLUGIN_ROOT}/shared/discovery.md` and
   build it. If injected, use it as-is (do not re-run discovery).
2. **Filter**: read `${CLAUDE_PLUGIN_ROOT}/shared/detection/10-container-iac.md`. Drop any checklist item whose
   `applies_to` shares no archetype with `discovery_context.archetypes` → emit it with
   `status: "skipped"`.
3. **Detect (two-stage, spec §5a.2 / §9a.4)**:
   a. For each applicable item, run its `signals` (ripgrep) to get candidate `file:line`.
      Prefer external-tool output if available. Do NOT read the whole repo.
   b. Read only candidate snippets; apply each item's `confirm` rule. Assign severity
      honoring any severity floors. Consult `${CLAUDE_PLUGIN_ROOT}/shared/detection/examples/10-container-iac.md` only
      when a candidate is ambiguous.
4. **Emit**: produce one `AuditResult` JSON object conforming to `${CLAUDE_PLUGIN_ROOT}/shared/schema.json` with
   `audit: "container_iac"`, `iso_characteristic: "Portability"`, the checklist (with
   statuses), and findings. Leave `score` as `0` — the engine computes it.
   - With `--json` or as a subagent: output ONLY the JSON.
   - Standalone: also print a short markdown summary (counts + top findings).

Return only valid JSON when invoked as a subagent.
