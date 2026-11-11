# Agent invocation — manual test checklist

Automated tests only check the skill files. Whether an agent **picks** the right skill and
**runs** it correctly can only be checked by hand. Run this checklist in Cursor (primary
target) before releasing a change to skill descriptions, frontmatter or the orchestrator's
"Choosing what to run" rules. Other agents: same prompts, adjust the invocation syntax.

## Setup

1. Make a small throwaway project with known problems:
   ```bash
   mkdir audit-playground && cd audit-playground && git init -q
   curl -sO https://raw.githubusercontent.com/appuk45/claude-codebase-audit/main/codebase-audit/test-fixture/bad_views.py
   ```
2. Install the version under test into it, for Cursor:
   ```bash
   # a branch under review
   npx skills add https://github.com/appuk45/claude-codebase-audit/tree/<branch-name> -a cursor
   # or a release
   npx skills add https://github.com/appuk45/claude-codebase-audit/tree/vX.Y.Z -a cursor
   ```
3. Open the folder in Cursor and start a **new** Agent chat (skills load at chat start).
4. Delete `.codebase-audit/`, `audit-report.*` between runs so results don't carry over.

## Checklist

Record what happened in **Actual**; mark **Pass** ✅/❌.

| # | Prompt | Expected | Actual | Pass |
|---|---|---|---|---|
| 0 | Type `/` in the chat | `codebase-audit` and all 11 `audit-*` skills are listed (proves Cursor loads skills from where `npx skills` installed them) | | |
| 1 | `Audit this codebase` | `codebase-audit` starts; shows the dimension menu and waits | | |
| 2 | `Full audit, all dimensions, no questions` | `codebase-audit` runs all applicable dimensions with no menu; writes `audit-report.html` and `audit-report.md` | | |
| 3 | `Audit only security and performance` | `codebase-audit` runs exactly `security` and `performance`; no menu | | |
| 4 | `/audit-security` | the security skill runs on its own; prints a short summary + JSON | | |
| 5 | `Check this repo for SQL injection` | either `codebase-audit` restricted to security, or no skill (a direct answer). **Must not** start `audit-security` on its own or run all 11 dimensions | | |
| 6 | `Review the get_orders function in bad_views.py for performance` | no audit skill starts; a normal code review answer | | |
| 7 | `How does the codebase-audit scoring work?` | answered from the docs; no audit run | | |
| 8 | *(optional)* Cursor CLI headless run asking to run the codebase-audit skill | no menu; runs to completion and writes the reports | | |

## Recording results

Copy the table into the PR (or an issue) with the agent name and version, the install command
used, and the date. A ❌ on 0, 2, 3, 5 or 6 blocks the release; others are follow-ups.
