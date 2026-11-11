"""Release rules, enforced in CI.

PR into main (release-gate check):
    python -m tools.release_gate --head "$GITHUB_HEAD_REF"
Push to main (release workflow):
    python -m tools.release_gate --release      # prints tag=vX.Y.Z (also to $GITHUB_OUTPUT)

Rules: the version files agree; the head branch is `release/vX.Y.Z` matching the version, or
`fix/*` (hotfix); the version is higher than the latest `v*` tag; in --release mode the tag
must not exist yet (every change to main must be a new version).
"""

import argparse
import os
import re
import subprocess
import sys

from tools.versioning import REPO_ROOT, engine_version, latest_tag, parse, plugin_version

_RELEASE_BRANCH_RE = re.compile(r"^release/v(\d+\.\d+\.\d+)$")


def version_errors(plugin_v, engine_v):
    errors = []
    try:
        parse(plugin_v)
    except ValueError as e:
        errors.append(f"plugin.json: {e}")
    if plugin_v != engine_v:
        errors.append(f"version mismatch: plugin.json {plugin_v} != engine {engine_v} "
                      "(use python -m tools.bump_version)")
    return errors


def pr_errors(head, plugin_v, engine_v, tags):
    """Problems with a PR from branch `head` into main. Empty list = OK."""
    errors = version_errors(plugin_v, engine_v)
    m = _RELEASE_BRANCH_RE.match(head or "")
    if m:
        if m.group(1) != plugin_v:
            errors.append(f"branch {head} does not match version {plugin_v}")
    elif not (head or "").startswith("fix/"):
        errors.append(f"PRs into main must come from release/vX.Y.Z or fix/* (hotfix), "
                      f"not {head!r}")
    errors += _newer_errors(plugin_v, tags)
    return errors


def release_errors(plugin_v, engine_v, tags):
    """Problems with releasing the current main. Empty list = OK."""
    errors = version_errors(plugin_v, engine_v)
    if f"v{plugin_v}" in tags:
        errors.append(f"tag v{plugin_v} already exists: bump the version for every change "
                      "to main (python -m tools.bump_version)")
    else:
        errors += _newer_errors(plugin_v, tags)
    return errors


def _newer_errors(plugin_v, tags):
    latest = latest_tag(tags)
    try:
        if latest and parse(plugin_v) <= parse(latest[1:]):
            return [f"version {plugin_v} is not higher than the latest release {latest}"]
    except ValueError:
        pass          # reported by version_errors
    return []


def git_tags(repo_root=REPO_ROOT):
    out = subprocess.run(["git", "tag", "--list", "v*"], cwd=repo_root,
                         capture_output=True, text=True, check=True).stdout
    return [t.strip() for t in out.splitlines() if t.strip()]


def main(argv=None):
    ap = argparse.ArgumentParser(prog="tools.release_gate")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--head", help="PR head branch (PR into main)")
    mode.add_argument("--release", action="store_true", help="push to main: release checks")
    args = ap.parse_args(argv)

    plugin_v, engine_v, tags = plugin_version(), engine_version(), git_tags()
    errors = (release_errors(plugin_v, engine_v, tags) if args.release
              else pr_errors(args.head, plugin_v, engine_v, tags))
    for e in errors:
        print(f"RELEASE GATE FAIL: {e}", file=sys.stderr)
    if errors:
        return 1
    print(f"tag=v{plugin_v}")
    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a", encoding="utf-8") as fh:
            fh.write(f"tag=v{plugin_v}\n")
    latest = latest_tag(tags)
    print(f"ok: v{plugin_v} (latest release: {latest or 'none'})", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
