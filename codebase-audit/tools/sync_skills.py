"""Copy the shared source-of-truth files into each skill folder.

Why: the Agent Skills standard (and the `npx skills` installer) installs each skill
folder on its own — nothing outside `skills/<name>/` is shipped. `shared/` stays the
single place to edit; this tool generates the per-skill copies under
`skills/*/references/` and the engine's bundled schema.

    python -m tools.sync_skills           # write copies (+ regenerate compliance map)
    python -m tools.sync_skills --check   # exit 1 if any copy is missing/stale/extra
"""

import argparse
import sys
from pathlib import Path

from tools.compliance import build_map, render_map_md

ROOT = Path(__file__).resolve().parent.parent
SHARED = ROOT / "shared"
SKILLS = ROOT / "skills"
ORCHESTRATOR = "codebase-audit"

# (skill dir, detection spec stem)
DIMENSIONS = [
    ("audit-performance", "01-performance"),
    ("audit-security", "02-security"),
    ("audit-enterprise", "03-enterprise"),
    ("audit-issues", "04-issues"),
    ("audit-architecture", "05-architecture"),
    ("audit-dependencies", "06-dependencies"),
    ("audit-i18n", "07-i18n"),
    ("audit-api", "08-api"),
    ("audit-resilience", "09-resilience"),
    ("audit-container-iac", "10-container-iac"),
    ("audit-observability", "11-observability"),
]

_DIM_COMMON = ["discovery.md", "schema.json", "scoring.md"]
_ORCH_COMMON = _DIM_COMMON + ["config-schema.md", "compliance-map.md"]


def _spec_files(stem):
    return [
        (SHARED / "detection" / f"{stem}.md", Path("detection") / f"{stem}.md"),
        (SHARED / "detection" / "examples" / f"{stem}.md",
         Path("detection") / "examples" / f"{stem}.md"),
    ]


def expected_files():
    """Map destination path -> source path for every generated file."""
    out = {}
    for skill, stem in DIMENSIONS:
        ref = SKILLS / skill / "references"
        for name in _DIM_COMMON:
            out[ref / name] = SHARED / name
        for src, rel in _spec_files(stem):
            out[ref / rel] = src
    ref = SKILLS / ORCHESTRATOR / "references"
    for name in _ORCH_COMMON:
        out[ref / name] = SHARED / name
    for _, stem in DIMENSIONS:
        for src, rel in _spec_files(stem):
            out[ref / rel] = src
    out[SKILLS / ORCHESTRATOR / "scripts" / "engine" / "schema.json"] = SHARED / "schema.json"
    return out


def _managed_dirs():
    return [SKILLS / s / "references" for s, _ in DIMENSIONS] + [
        SKILLS / ORCHESTRATOR / "references"]


def check():
    """Return a list of human-readable drift problems (empty = in sync)."""
    problems = []
    expected = expected_files()
    compliance = render_map_md(build_map(SHARED / "detection"))
    if (SHARED / "compliance-map.md").read_text() != compliance:
        problems.append("shared/compliance-map.md is stale (run python -m tools.sync_skills)")
    for dst, src in expected.items():
        if not dst.exists():
            problems.append(f"missing: {dst.relative_to(ROOT)}")
        elif dst.read_bytes() != src.read_bytes():
            problems.append(f"stale: {dst.relative_to(ROOT)} (source {src.relative_to(ROOT)})")
    for d in _managed_dirs():
        if d.exists():
            for f in d.rglob("*"):
                if f.is_file() and f not in expected:
                    problems.append(f"unexpected: {f.relative_to(ROOT)}")
    return problems


def sync():
    (SHARED / "compliance-map.md").write_text(render_map_md(build_map(SHARED / "detection")))
    expected = expected_files()
    for d in _managed_dirs():
        if d.exists():
            for f in d.rglob("*"):
                if f.is_file() and f not in expected:
                    f.unlink()
    for dst, src in expected.items():
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(src.read_bytes())
    return len(expected)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="tools.sync_skills")
    ap.add_argument("--check", action="store_true", help="verify only; exit 1 on drift")
    args = ap.parse_args(argv)
    if args.check:
        problems = check()
        for p in problems:
            print(p, file=sys.stderr)
        print("in sync" if not problems else f"{len(problems)} problem(s)")
        return 1 if problems else 0
    n = sync()
    print(f"Synced {n} files into skills/*/references and the engine")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
