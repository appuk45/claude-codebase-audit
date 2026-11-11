"""Set the release version everywhere it appears.

    python -m tools.bump_version 1.2.0

Updates `.claude-plugin/plugin.json`, the engine's `__version__`, and every
`claude-codebase-audit@vX.Y.Z` install snippet in README.md / USAGE.md.
"""

import argparse
import re
import sys
from pathlib import Path

from tools.versioning import (DOCS, ENGINE_INIT, ENGINE_RE, PIN_RE, PLUGIN_JSON, PLUGIN_ROOT,
                              REPO_ROOT, parse)

# First "version" key in plugin.json; keeps the file's formatting intact.
_PLUGIN_VERSION_RE = re.compile(r'("version"\s*:\s*")[^"]*(")')


def _sub(path, pattern, repl, count=0, required=True):
    """Apply one regex substitution to a file. Returns True if the file changed."""
    text = path.read_text(encoding="utf-8")
    new, n = pattern.subn(repl, text, count=count)
    if required and n == 0:
        raise ValueError(f"version pattern not found in {path}")
    if new == text:
        return False
    path.write_text(new, encoding="utf-8")
    return True


def bump(version, plugin_root=PLUGIN_ROOT, repo_root=REPO_ROOT):
    """Write `version` into every version location. Returns the files that changed."""
    parse(version)
    plugin_root, repo_root = Path(plugin_root), Path(repo_root)
    edits = [
        (plugin_root / PLUGIN_JSON, _PLUGIN_VERSION_RE, rf"\g<1>{version}\g<2>", 1, True),
        (plugin_root / ENGINE_INIT, ENGINE_RE, f'__version__ = "{version}"', 0, True),
    ] + [
        (repo_root / doc, PIN_RE, rf"\g<1>{version}", 0, False)
        for doc in DOCS if (repo_root / doc).exists()
    ]
    return [path for path, pattern, repl, count, required in edits
            if _sub(path, pattern, repl, count, required)]


def main(argv=None):
    ap = argparse.ArgumentParser(prog="tools.bump_version")
    ap.add_argument("version", help="new version, X.Y.Z (no leading v)")
    args = ap.parse_args(argv)
    try:
        changed = bump(args.version)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    for p in changed:
        print(f"updated {p}")
    print(f"version is now {args.version}" + ("" if changed else " (already set)"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
