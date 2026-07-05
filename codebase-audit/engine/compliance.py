"""Generate the compliance map from detection specs' inline compliance_refs (spec 9a.2)."""

import re
import sys
from pathlib import Path

_ITEM_RE = re.compile(r"^###\s+([a-z][a-z0-9_]+)\b")
_REFS_RE = re.compile(r"^\s*-\s+\*\*compliance_refs:\*\*\s*(.+?)\s*$")


def parse_spec(text):
    """Map each `### <item_id>` to its `compliance_refs` list, if present."""
    mapping = {}
    current = None
    for line in text.splitlines():
        m = _ITEM_RE.match(line)
        if m:
            current = m.group(1)
            continue
        r = _REFS_RE.match(line)
        if r and current:
            refs = [x.strip() for x in r.group(1).split(",") if x.strip()]
            mapping[current] = refs
    return mapping


def build_map(detection_dir):
    """Merge parse_spec over every NN-*.md detection spec (sorted)."""
    mapping = {}
    for path in sorted(Path(detection_dir).glob("[0-9][0-9]-*.md")):
        mapping.update(parse_spec(path.read_text()))
    return mapping


def render_map_md(mapping):
    lines = [
        "# Compliance Map",
        "",
        "Generated from the detection specs' inline `compliance_refs` "
        "(source of truth — do not hand-edit). Regenerate: `python -m engine.compliance`.",
        "",
        "| checklist_id | controls |",
        "|---|---|",
    ]
    for cid in sorted(mapping):
        lines.append(f"| {cid} | {', '.join(mapping[cid])} |")
    lines.append("")
    return "\n".join(lines)


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    root = Path(__file__).parent.parent
    detection = Path(argv[0]) if len(argv) > 0 else root / "shared" / "detection"
    out = Path(argv[1]) if len(argv) > 1 else root / "shared" / "compliance-map.md"
    mapping = build_map(detection)
    out.write_text(render_map_md(mapping))
    print(f"Wrote {out} ({len(mapping)} checklist ids)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
