import argparse
import sys
from pathlib import Path

import yaml

from engine.validate import load_results, ValidationFailure
from engine.scoring import score_dimension, overall_score
from engine.gate import count_severities, apply_suppressions, evaluate_gate
from engine.report_md import render_markdown
import json as _json
import datetime as _dt
from pathlib import Path as _Path

from engine.sarif import to_sarif
from engine.html import render_html

DEFAULT_GATE = {"max_high": 0, "max_medium": None, "max_low": None}


def _load_config(path):
    if not path:
        return {"gate": dict(DEFAULT_GATE), "suppress": []}
    cfg = yaml.safe_load(Path(path).read_text()) or {}
    gate = {**DEFAULT_GATE, **(cfg.get("gate") or {})}
    return {"gate": gate, "suppress": cfg.get("suppress") or []}


def main(argv=None):
    ap = argparse.ArgumentParser(prog="engine.cli")
    ap.add_argument("--results", required=True, help="path to AuditResult[] JSON")
    ap.add_argument("--out", required=True, help="path to write the markdown report")
    ap.add_argument("--config", help="path to .codebase-audit.yml")
    ap.add_argument("--total-lines", type=int, default=1, help="discovery_context.total_lines")
    ap.add_argument("--ci", action="store_true", help="enforce gate + set exit code")
    ap.add_argument("--formats", default="md",
                    help="comma list of outputs: md,sarif,html (default md)")
    ap.add_argument("--sarif-out", default="audit-report.sarif")
    ap.add_argument("--html-out", default="audit-report.html")
    ap.add_argument("--discovery", help="path to discovery_context JSON (for HTML meta)")
    args = ap.parse_args(argv)

    try:
        results = load_results(args.results)
    except ValidationFailure as e:
        print(f"validation error: {e}", file=sys.stderr)
        return 2

    config = _load_config(args.config)
    gated_results = apply_suppressions(results, config["suppress"])

    per_dim = {r["audit"]: score_dimension(r, args.total_lines) for r in gated_results}
    overall = overall_score(list(per_dim.values()))
    counts = count_severities(gated_results)

    formats = [f.strip() for f in args.formats.split(",") if f.strip()]

    if "md" in formats:
        Path(args.out).write_text(render_markdown(gated_results, per_dim, overall, counts))
    if "sarif" in formats:
        _Path(args.sarif_out).write_text(_json.dumps(to_sarif(gated_results), indent=2))
    if "html" in formats:
        meta = {"project": _Path.cwd().name, "date": _dt.date.today().isoformat()}
        if args.discovery:
            disc = _json.loads(_Path(args.discovery).read_text())
            meta["project"] = disc.get("project_name", meta["project"])
            meta["languages"] = disc.get("languages", [])
            meta["archetypes"] = disc.get("archetypes", [])
        asset = _Path(__file__).parent / "assets" / "chart.umd.min.js"
        chartjs = asset.read_text() if asset.exists() else ""
        _Path(args.html_out).write_text(
            render_html(gated_results, per_dim, overall, counts, meta, chartjs))

    breaches = evaluate_gate(counts, config["gate"]) if args.ci else []
    if breaches:
        for sev, actual, limit in breaches:
            print(f"GATE FAIL: {sev} findings {actual} exceed limit {limit}")
        return 1
    print(f"Audit report written to {args.out} (overall {overall})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
