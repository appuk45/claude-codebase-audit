# Releasing codebase-audit

Users install a pinned version with:

```bash
npx skills add appuk45/claude-codebase-audit@vX.Y.Z
```

A tag is created **automatically** when a release or hotfix is merged into `main`. Never
create, move, or delete a `v*` tag by hand — a pinned version must never change.

## Branch flow

```
feature/* fix/* refactor/* chore/*  ──squash or merge──▶  dev
dev  ──merge commit──▶  release/vX.Y.Z  ──merge commit──▶  main  ──(auto)──▶  tag vX.Y.Z
main ──merge commit──▶  dev            (back-merge after every release / hotfix)
```

| Branch | Created from | Merges into | Merge type |
|---|---|---|---|
| `feature/` `fix/` `refactor/` `chore/` | `dev` | `dev` | squash or merge |
| `release/vX.Y.Z` | `dev` | `main` | **merge commit** |
| `fix/<name>` (hotfix) | `main` | `main` | **merge commit** |
| back-merge | `main` | `dev` | **merge commit** |

Never squash into `main`, into `release/*`, or a back-merge: squashing gives the target new
commit IDs for the same content, so the next release PR re-shows old commits and conflicts.

## Normal release checklist

1. Cut the release branch from an up-to-date `dev`:
   ```bash
   git switch dev && git pull && git switch -c release/v1.2.0
   ```
2. Bump the version (plugin.json, engine `__version__`, README/USAGE install snippets):
   ```bash
   cd codebase-audit && python -m tools.bump_version 1.2.0
   ```
3. Commit, push, and open a PR `release/v1.2.0` → `main`. Only stabilisation fixes go on
   this branch from now on.
4. Wait for `ci` and `release-gate` to pass. `release-gate` rejects a branch name that does
   not match the version, or a version not higher than the latest tag.
5. Merge with **Create a merge commit**.
6. The `release` workflow runs on `main`: checks the tag is new, runs the tests, creates tag
   `v1.2.0` and a GitHub release with generated notes. Check it went green.
7. Back-merge: open a PR `main` → `dev`, merge with a merge commit.
8. Delete `release/v1.2.0`.

## Hotfix checklist

1. `git switch main && git pull && git switch -c fix/<name>`
2. Fix, then bump the **patch** version: `python -m tools.bump_version 1.2.1`.
3. PR `fix/<name>` → `main`; merge with a merge commit → tag `v1.2.1` is created.
4. Back-merge `main` → `dev` (merge commit); delete the fix branch.

## If the release workflow fails

- **"tag … already exists"** — something reached `main` without a version bump. Bump the
  version on a `fix/*` branch and merge it as a hotfix.
- **Tests or sync check fail** — nothing was tagged (the tag is created last). Fix on a
  `fix/*` branch from `main` and merge it; that run creates the tag.

## GitHub settings (owner applies these once)

Settings → Rules → Rulesets. Required checks only become selectable after they have run once.

**`main`**
- Require a pull request before merging.
- Require status checks: `test (3.11)`, `test (3.12)`, `test (3.13)`, `install-smoke`,
  `release-gate`.
- Block force pushes; restrict deletions.
- Allowed merge methods: **Merge** only.

**`dev`**
- Require a pull request; require `test (3.11)`, `test (3.12)`, `test (3.13)`,
  `install-smoke`.
- Block force pushes; restrict deletions.
- Allowed merge methods: Merge and Squash.

**`release/**`**
- Require a pull request; require the `test (…)` checks; block force pushes.

**Tags `v*`** (tag ruleset)
- Restrict updates and deletions, so a published version can never change.
- If your plan offers **immutable releases** (Settings → General → Releases), enable it.

**Repository**
- Keep `main` as the default branch, so an unpinned install gets the latest release.
