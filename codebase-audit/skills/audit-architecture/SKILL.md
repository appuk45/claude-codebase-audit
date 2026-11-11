---
name: audit-architecture
description: "Static whole-repository architecture audit, one dimension of codebase-audit — checks coupling, layering violations, import cycles, scalability limits. Use when the user explicitly asks to audit or scan the repository for architecture only, or invokes /audit-architecture. Not for reviewing a single file, function or diff. Normally run by the codebase-audit skill as part of a full audit; emits AuditResult JSON."
disable-model-invocation: true
compatibility: Requires a POSIX shell (bash/zsh; Git Bash or WSL on Windows). ripgrep recommended. Works in any Agent Skills client (Claude Code, Codex, Cursor, GitHub Copilot, ...).
---

# /audit-architecture

Audit the current working directory for the Architecture & Scalability dimension.

Paths in this file are relative to this skill's own directory (the folder that
contains this SKILL.md), not to the repository being audited. Run all detection
commands in the repository being audited (the current working directory).

## Inputs
- Optional `discovery_context` (JSON) injected by the orchestrator.
- Optional output path (from the orchestrator): write the JSON there instead of
  printing it.
- `--json`, or a request for JSON only: emit only the JSON, no markdown summary.

## Steps

1. **Discovery**: if `discovery_context` was NOT injected, follow `references/discovery.md` and
   build it. If injected, use it as-is (do not re-run discovery).
2. **Filter**: read `references/detection/05-architecture.md`. Drop any checklist item whose
   `applies_to` shares no archetype with `discovery_context.archetypes` → emit it with
   `status: "skipped"`.
3. **Detect (two-stage, spec §5a.2 / §9a.4)**:
   a. For each applicable item, run its `signals` (ripgrep) to get candidate `file:line`.
      Prefer external-tool output if available. Do NOT read the whole repo.
   b. Read only candidate snippets; apply each item's `confirm` rule. Assign severity
      honoring any severity floors. Consult `references/detection/examples/05-architecture.md` only
      when a candidate is ambiguous.
4. **Emit**: produce one `AuditResult` JSON object conforming to `references/schema.json` with
   `audit: "architecture"`, `iso_characteristic: "Reliability"`, the checklist (with
   statuses), and findings. Leave `score` as `0` — the engine computes it.
   - If an output path was given: write ONLY the JSON object to it (UTF-8), then reply
     with one line: `<audit key>: <n> findings -> <path>`.
   - With `--json`, when asked for JSON only, or as a subagent without an output path:
     output ONLY the JSON.
   - Standalone: also print a short markdown summary (counts + top findings).

When invoked as a subagent, return only valid JSON — or, when an output path was
given, only the one-line confirmation.
