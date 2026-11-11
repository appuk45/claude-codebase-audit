# Install With or Without a Version — Hotfix v1.1.1

**Date:** 2026-11-11 · **Status:** Approved (spec + plan) · **Route:** hotfix `fix/pinned-install` from `main`

## Problem

After v1.1.0 was released, the documented pinned install
`npx skills add appuk45/claude-codebase-audit@v1.1.0` installed **nothing** on `skills` 1.7.6:
the CLI reads `@v1.1.0` both as the git ref and as a skill-name filter
("No matching skills found for: v1.1.0"). CI did not catch it because `install-smoke` installs
from a local path, never from a published tag.

Measured from GitHub against tag `v1.1.0`:

| Command | skills 1.7.6 | skills 1.8.1 | lockfile `ref` |
|---|---|---|---|
| `appuk45/claude-codebase-audit` | ✅ 106 files | ✅ 106 files | none (follows latest release) |
| `appuk45/claude-codebase-audit@v1.1.0` | ❌ nothing installed | ✅ | `v1.1.0` (1.8.1) |
| `…@v1.1.0 --skill '*'` | ⚠️ installs | — | none (not actually pinned) |
| `https://github.com/appuk45/claude-codebase-audit/tree/v1.1.0` | ✅ | ✅ | `v1.1.0` |
| `https://github.com/appuk45/claude-codebase-audit.git#v1.1.0` | ✅ | — | `v1.1.0` |

## Decisions

- **Default install has no version:** `npx skills add appuk45/claude-codebase-audit` → the
  default branch `main`, which only ever holds releases. `npx skills update` moves it to the
  newest release. This makes the `main` ruleset (releases only) load-bearing.
- **Pinned install uses the tree URL:** `npx skills add https://github.com/appuk45/claude-codebase-audit/tree/vX.Y.Z`
  — works on both CLI versions and records `ref` in the lockfile. Recommended for teams and CI.
- The short `@vX.Y.Z` form is removed from all docs (a test forbids it as a command).
- `bump_version` keeps the pinned example current by matching `…/tree/vX.Y.Z`.
- `release.yml` gains a final step: install the just-published tag from GitHub with the pinned
  URL (`skills@1.7.6`, the stricter CLI) and assert 12 skills, >100 files, and lockfile
  `ref == tag`. It runs after publishing (the tag must exist), so a failure turns the run red
  rather than blocking the release.

## Out of scope

Changing the CLI version pinned in CI; testing GitHub installs in PR CI (a PR's code is not on
GitHub's `main` yet, so it would test the wrong code).

## Plan (executed on `fix/pinned-install`)

1. This record. 2. README/USAGE install sections. 3. RELEASING (commands, hotfix back-merge
note, verify-step failure). 4. `tools/versioning.PIN_RE`. 5. `tests/test_bump_version.py` (+ a
test that no doc uses the short form as a command). 6. `release.yml` verify step. 7.
`bump_version 1.1.1`. 8. CLAUDE.md status/commands. Verify: pytest, sync check,
`release_gate --head fix/pinned-install`, actionlint, the verify step run locally against
`v1.1.0` (pass) and a missing tag (fail). Then PR → `main`; owner merges with a merge commit;
open back-merge PR #8 (source `main`) picks up the hotfix.
