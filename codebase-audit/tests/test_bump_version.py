import json
import shutil
from pathlib import Path

import pytest

from tools.bump_version import bump
from tools.versioning import ENGINE_INIT, PLUGIN_JSON, engine_version, plugin_version

ROOT = Path(__file__).parents[1]


@pytest.fixture
def repo(tmp_path):
    """Minimal copy of the files bump_version touches."""
    plugin = tmp_path / "codebase-audit"
    for rel in (PLUGIN_JSON, ENGINE_INIT):
        (plugin / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / rel, plugin / rel)
    (tmp_path / "README.md").write_text(
        "npx skills add appuk45/claude-codebase-audit@v1.1.0\n"
        "npx skills add appuk45/claude-codebase-audit@v1.1.0 -a codex\n")
    (tmp_path / "USAGE.md").write_text("no pins here\n")
    return tmp_path, plugin


def test_bump_updates_every_location(repo):
    root, plugin = repo
    changed = bump("2.3.4", plugin, root)
    assert plugin_version(plugin) == "2.3.4"
    assert engine_version(plugin) == "2.3.4"
    readme = (root / "README.md").read_text()
    assert readme.count("claude-codebase-audit@v2.3.4") == 2 and "v1.1.0" not in readme
    assert {p.name for p in changed} == {"plugin.json", "__init__.py", "README.md"}
    # plugin.json keeps its other fields and stays valid JSON
    data = json.loads((plugin / PLUGIN_JSON).read_text())
    assert data["name"] == "codebase-audit" and isinstance(data["author"], dict)


def test_bump_same_version_is_a_noop(repo):
    root, plugin = repo
    current = plugin_version(plugin)          # fixture README already pins v1.1.0
    assert current == "1.1.0"
    assert bump(current, plugin, root) == []


@pytest.mark.parametrize("bad", ["v1.2.0", "1.2", "1.2.3-rc1", "01.2.3", "", "latest"])
def test_bump_rejects_non_semver(repo, bad):
    root, plugin = repo
    with pytest.raises(ValueError):
        bump(bad, plugin, root)
    assert plugin_version(plugin) == engine_version(plugin)   # untouched


def test_real_repo_docs_pin_the_current_version():
    """README/USAGE install snippets must match the release version."""
    from tools.versioning import PIN_RE, REPO_ROOT
    version = plugin_version()
    for doc in ("README.md", "USAGE.md"):
        for m in PIN_RE.finditer((REPO_ROOT / doc).read_text(encoding="utf-8")):
            assert m.group(0).endswith(f"@v{version}"), f"{doc}: {m.group(0)}"
