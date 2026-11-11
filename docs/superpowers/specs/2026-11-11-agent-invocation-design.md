# Agent Invocation in Cursor and Other Agents — Design

**Date:** 2026-11-11 · **Status:** Approved (spec + plan) · **Branch:** `feature/agent-invocation` → `dev` → v1.2.0

## Problem

The skills were written for Claude Code: mode was chosen only by flags (`--all`, `--ci`,
`--json`), the orchestrator could block on a menu in headless runs, and descriptions said what
a skill emits rather than when to use it. Other agents choose skills from `name` +
`description` alone, and pass arguments differently (or not at all).

Researched invocation (2026-11): Claude Code and Cursor `/skill-name`; Codex `$skill-name` or
`/skills`; Kiro/Antigravity `/skill-name`; Augment/Kimi `/skill:name`. All also pick skills
implicitly from the description. Copilot and Gemini CLI: not confirmed.

## Decisions

1. **Implicit invocation (owner choice b):** only `codebase-audit` may be auto-selected. The
   11 `audit-*` skills get top-level `disable-model-invocation: true` — documented by Cursor
   (https://cursor.com/docs/skills) and used by Claude Code. Verified: `npx skills` 1.7.6 and
   1.8.1 install such skills and keep the field. The orchestrator does not invoke dimension
   skills (it reads specs from its own `references/`), so orchestration is unaffected.
   - Cost: the reference validator (`skills-ref` 0.1.1 `agentskills validate`) rejects unknown
     top-level fields; under `metadata` it passes but Cursor would not read it. Chosen: top
     level; tests allow exactly this one extra field.
   - Agents that ignore the field may still auto-select dimension skills; their descriptions
     say "Normally run by the codebase-audit skill" to discourage it.
2. **Mode selection (owner choice A+B):** orchestrator section "Choosing what to run" —
   request (words or flags) > `.codebase-audit.yml` (`mode: interactive|all|ci`,
   `dimensions`) > defaults. Phrase mapping for full/CI/no-questions/named dimensions. Never
   show a menu nobody can answer (headless, CI, "don't ask") — treat as `all`.
3. **Descriptions:** all 12 rewritten as *what + "Use when …" + keywords + "Not for …"*.
4. **Docs:** per-agent "start the audit" table in README/USAGE; `mode` in config docs.
5. **Manual checklist** `docs/testing/agent-invocation.md` (Cursor first, 8 prompts + a
   visibility check) — the only way to verify real selection behaviour.

## Out of scope

Codex explicit-only setting (said to live in `agents/openai.yaml`; unconfirmed, untestable
here); the two-level reference chain and `codebase-audit/skills/` location; Copilot/Gemini
specifics.

## Unknowns resolved only by the manual test

Whether Cursor loads project skills from `.agents/skills/` (where `npx skills` installs them
for Cursor — Cursor's docs mention `.cursor/skills/`); how reliably models follow the
plain-language mode rules.

## Plan

1. This record. 2. 11 dimension SKILL.md: field + descriptions + JSON wording. 3. Orchestrator
SKILL.md: description, "Choosing what to run", steps 1 and 4. 4. `shared/config-schema.md`
`mode` + sync. 5. `tests/test_packaging.py` invocation contract. 6. README/USAGE. 7.
`docs/testing/agent-invocation.md`. 8. CLAUDE.md. 9. Verify: pytest, sync check, validator
(expect only the known field on 11 dims), description lengths, `npx skills add -a cursor`
keeps the field. 10. Commit, push, PR → `dev`; owner runs the Cursor checklist against the
branch install before merging.
