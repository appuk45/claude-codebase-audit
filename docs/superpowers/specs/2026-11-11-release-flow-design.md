# Release Branching & Versioned Releases — Design

**Date:** 2026-11-11
**Status:** Approved
**Plan:** `docs/superpowers/plans/2026-11-11-release-flow.md`

## Goal

Every change flows `feature|fix|refactor|chore` → `dev` → `release/vX.Y.Z` → `main`. Each
merge into `main` produces tag `vX.Y.Z` and a GitHub release automatically, so users pin with
`npx skills add appuk45/claude-codebase-audit@vX.Y.Z`.

## Branches

| Branch | Lifetime | Created from | Merges into |
|---|---|---|---|
| `main` | permanent, GitHub default, released code only | — | — |
| `dev` | permanent, integration | `main` (once) | `release/*` |
| `feature/` `fix/` `refactor/` `chore/` | until merged | `dev` | `dev` |
| `release/vX.Y.Z` | until released, then deleted | `dev` | `main` |
| `fix/*` as hotfix | until merged | `main` | `main`, then `main` → `dev` |

`main` stays the default branch, so an unpinned install gets the latest release, never `dev`.

## Normal release

1. Cut `release/vX.Y.Z` from `dev`.
2. Bump the version with `python -m tools.bump_version X.Y.Z` (updates `plugin.json`, the
   engine `__version__`, and the `@vX.Y.Z` install snippets in README/USAGE).
3. Stabilisation fixes only on the release branch.
4. PR into `main`; merge with a **merge commit**.
5. On push to `main`, the release workflow verifies the versions agree and that the tag does
   **not** exist yet (fails otherwise — every change to `main` must be a new version), runs
   the tests, then creates the tag and GitHub release with generated notes.
6. Back-merge `main` → `dev`; delete the release branch.

## Hotfix

`fix/<name>` from `main` → bump the patch version → PR into `main` → merge (auto-tagged) →
back-merge `main` → `dev`.

## Merge rules

- Work branches → `dev`: squash allowed.
- `dev` → `release/*`, `release/*` → `main`, `main` → `dev`: **merge commit only**. Squashing
  these gives the target branch new commit IDs for the same content, so later PRs re-show old
  commits and conflict.

## Automation

- `release.yml` triggers on push to `main` (not on tag push) and creates tag + release in the
  same job — a tag created by a workflow cannot trigger another workflow.
- `release-gate` check on PRs into `main`: head is `release/vX.Y.Z` (name matching the
  version) or `fix/*`; version > latest `v*` tag; version files agree.
- `ci.yml` runs on push/PR for `main`, `dev`, `release/**`.
- `tools/bump_version.py`, `tools/release_gate.py` (pure Python, unit-tested).
- `RELEASING.md` holds the checklists and the branch-protection settings.

## GitHub settings (applied by the owner)

- `main`: require PR; required checks `test (3.11)`, `test (3.12)`, `test (3.13)`,
  `install-smoke`, `release-gate`; block force-push and deletion; merge commit only.
- `dev`: require PR + the same checks minus `release-gate`; block force-push/deletion; allow
  squash and merge commit.
- `release/**`: require PR + tests; block force-push.
- Tags `v*`: block deletion and update (a pinned version must never change). Enable
  immutable releases if the plan offers it.

## Out of scope

Hand-written CHANGELOG (generated notes instead), signed tags, npm/PyPI publishing, automatic
back-merge PRs (a workflow-created PR would not run CI; the back-merge stays a manual
checklist item).
