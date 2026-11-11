"""Packaging contract: every skill folder is self-contained and Agent Skills-conformant,
so `npx skills add` (which installs only skill folders) yields a working install."""
import json
import re
from pathlib import Path

import yaml

from engine import __version__
from tools.sync_skills import check

ROOT = Path(__file__).parents[1]
SKILLS = sorted((ROOT / "skills").glob("*/SKILL.md"))
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
# Skill-relative file references written in SKILL.md bodies.
REF_RE = re.compile(r"`((?:references|scripts)/(?!\.\.\.)[^`\s*<>]+)`")


def _frontmatter(path):
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n"), f"{path} has no frontmatter"
    fm, body = text[4:].split("\n---\n", 1)
    return yaml.safe_load(fm), body


def test_twelve_skills_present():
    assert len(SKILLS) == 12


def test_frontmatter_follows_agent_skills_spec():
    for path in SKILLS:
        fm, _ = _frontmatter(path)
        name = fm["name"]
        assert NAME_RE.match(name) and len(name) <= 64, name
        assert name == path.parent.name, f"name must match directory: {path}"
        assert 0 < len(fm["description"]) <= 1024, path
        if "compatibility" in fm:
            assert len(fm["compatibility"]) <= 500, path


def test_no_tool_specific_or_out_of_skill_paths():
    for path in SKILLS:
        _, body = _frontmatter(path)
        assert "CLAUDE_PLUGIN_ROOT" not in body, path
        assert "shared/" not in body, f"{path} references files outside its folder"
        assert "/tmp/" not in body, f"{path} hard-codes a non-portable temp path"


def test_every_referenced_file_ships_inside_the_skill():
    for path in SKILLS:
        _, body = _frontmatter(path)
        for ref in REF_RE.findall(body):
            assert (path.parent / ref).exists(), f"{path.parent.name}: missing {ref}"


def test_skill_bodies_stay_small():
    for path in SKILLS:
        assert len(path.read_text(encoding="utf-8").splitlines()) < 500, path


def test_generated_copies_in_sync_with_shared():
    assert check() == []


def test_versions_agree():
    plugin = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text())
    assert plugin["version"] == __version__
