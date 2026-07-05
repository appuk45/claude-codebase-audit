from pathlib import Path
from engine.compliance import parse_spec, build_map, render_map_md

SAMPLE = """# Detection Spec 02 — Security

### sec_injection — No injection vulnerabilities
- **intent:** stuff
- **compliance_refs:** OWASP A05:2025, CWE-89, CWE-78

### sec_crypto — No weak crypto
- **compliance_refs:** OWASP A04:2025, CWE-327

## How to use
not an item
"""

def test_parse_spec_extracts_refs():
    m = parse_spec(SAMPLE)
    assert m["sec_injection"] == ["OWASP A05:2025", "CWE-89", "CWE-78"]
    assert m["sec_crypto"] == ["OWASP A04:2025", "CWE-327"]
    assert "How" not in m and "to" not in m

def test_build_map_over_real_specs():
    detection = Path(__file__).parents[2] / "shared" / "detection"
    m = build_map(detection)
    assert "sec_injection" in m
    assert "perf_n_plus_one" in m
    assert any("OWASP" in ref or "ISO25010" in ref or "CWE" in ref or "CIS" in ref
               for refs in m.values() for ref in refs)

def test_render_map_md_is_a_table():
    md = render_map_md({"sec_injection": ["OWASP A05:2025", "CWE-89"]})
    assert "| checklist_id | controls |" in md
    assert "| sec_injection | OWASP A05:2025, CWE-89 |" in md
