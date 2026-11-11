"""Shared helpers for reading and comparing the release version (dev-only, not shipped)."""

import json
import re
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = PLUGIN_ROOT.parent
PLUGIN_JSON = Path(".claude-plugin") / "plugin.json"
ENGINE_INIT = Path("skills") / "codebase-audit" / "scripts" / "engine" / "__init__.py"
DOCS = ["README.md", "USAGE.md"]          # relative to the repo root

SEMVER_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
ENGINE_RE = re.compile(r'^__version__ = "([^"]*)"$', re.M)
# Pinned-install example in the docs: .../claude-codebase-audit/tree/vX.Y.Z
PIN_RE = re.compile(r"(claude-codebase-audit/tree/v)\d+\.\d+\.\d+")


def parse(version):
    """'1.2.3' -> (1, 2, 3). Raises ValueError for anything that is not plain X.Y.Z."""
    m = SEMVER_RE.match(version or "")
    if not m:
        raise ValueError(f"not a plain X.Y.Z version: {version!r}")
    return tuple(int(p) for p in m.groups())


def plugin_version(plugin_root=PLUGIN_ROOT):
    return json.loads((Path(plugin_root) / PLUGIN_JSON).read_text(encoding="utf-8"))["version"]


def engine_version(plugin_root=PLUGIN_ROOT):
    m = ENGINE_RE.search((Path(plugin_root) / ENGINE_INIT).read_text(encoding="utf-8"))
    if not m:
        raise ValueError(f"no __version__ in {ENGINE_INIT}")
    return m.group(1)


def latest_tag(tags):
    """Highest vX.Y.Z among `tags` (strings), or None. Non-version tags are ignored."""
    best = None
    for t in tags:
        if not t.startswith("v"):
            continue
        try:
            v = parse(t[1:])
        except ValueError:
            continue
        if best is None or v > best:
            best = v
    return None if best is None else "v" + ".".join(map(str, best))
