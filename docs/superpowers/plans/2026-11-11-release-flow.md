# Release Flow — Implementation Plan

**Date:** 2026-11-11 · **Status:** Approved · **Spec:** `docs/superpowers/specs/2026-11-11-release-flow-design.md`

## Phase A — Prepare `dev`
- A1 Fast-forward `dev` to `main` (`git push origin origin/main:dev`). *(done)*
- A2 Verify PR #5 reduces to its 3 commits. *(done)*
- A3 Owner merges PR #5 into `dev`. *(done — merge commit `d079c5f`)*

## Phase B — `chore/release-flow` from `dev`
- B1 This spec → `docs/superpowers/specs/2026-11-11-release-flow-design.md`.
- B2 This plan → `docs/superpowers/plans/2026-11-11-release-flow.md`.
- B3 `codebase-audit/tools/bump_version.py` + `tests/test_bump_version.py`: one command
  updates `plugin.json`, engine `__version__`, README/USAGE `claude-codebase-audit@vX.Y.Z`;
  rejects non-`X.Y.Z`.
- B4 `codebase-audit/tools/release_gate.py` + `tests/test_release_gate.py`: head branch is
  `release/vX.Y.Z` (matching version) or `fix/*`; version > latest `v*` tag; version files
  agree. `--release` mode: fail if the tag already exists.
- B5 `.github/workflows/release-gate.yml`: PRs into `main`, full history + tags.
- B6 `.github/workflows/release.yml`: on push to `main`; one run at a time; gate `--release`,
  sync check, tests, `gh release create vX.Y.Z --target <sha> --generate-notes`.
- B7 `.github/workflows/ci.yml`: push/PR on `main`, `dev`, `release/**`.
- B8 `RELEASING.md`: release + hotfix checklists, merge rules, branch-protection settings.
- B9 `CLAUDE.md` (branch table: `release/vX.Y.Z`, hotfix, work branches from `dev`),
  `README.md` (Releasing → `RELEASING.md`).
- B10 Verify: pytest, `sync_skills --check`, gate scenarios, release job shell steps locally
  (minus `gh release create`), `actionlint` if installable.
- B11 Commit, push, PR `chore/release-flow` → `dev`.

## Phase C — Owner, on GitHub
- C1 Merge the PR into `dev`.
- C2 Apply the rulesets from the spec (after `release-gate` has run once, so it is selectable).

## Phase D — First release, v1.1.0
- D1 Cut `release/v1.1.0` from `dev`, `bump_version 1.1.0` (no-op), push, PR → `main`.
- D2 Owner merges with a merge commit.
- D3 Verify tag `v1.1.0` + release; `npx skills add appuk45/claude-codebase-audit@v1.1.0` in a
  scratch project.
- D4 Open back-merge PR `main` → `dev`.
- D5 Owner merges (merge commit) and deletes `release/v1.1.0`.

## Risks
- The release workflow first runs for real at D3; a failure there is fixed via a hotfix PR.
  The tag is created last, so no partial tag is left behind.
- Until C2 is applied, nothing enforces the flow.
