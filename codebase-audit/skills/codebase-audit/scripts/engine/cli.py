import argparse
import datetime as _dt
import json
import sys
from pathlib import Path

import yaml

from engine import __version__
from engine.validate import load_results, load_results_dir, ValidationFailure
from engine.scoring import score_dimension, overall_score
from engine.gate import count_severities, apply_suppressions, evaluate_gate, errored_dimensions
from engine.report_md import render_markdown
from engine.sarif import to_sarif
from engine.html import render_html

DEFAULT_GATE = {"max_high": 0, "max_medium": None, "max_low": None, "fail_on_error": True}


def _load_config(path):
    if not path:
        return {"gate": dict(DEFAULT_GATE), "suppress": []}
    cfg = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    gate = {**DEFAULT_GATE, **(cfg.get("gate") or {})}
    return {"gate": gate, "suppress": cfg.get("suppress") or []}


def main(argv=None):
    ap = argparse.ArgumentParser(prog="codebase-audit-engine")
    ap.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--results", help="path to a JSON array of AuditResult objects")
    src.add_argument("--results-dir",
                     help="directory of <audit>.json files, one AuditResult each")
    ap.add_argument("--expect", default="",
                    help="comma list of audit keys that must be present (with --results-dir); "
                         "missing ones are recorded as errored dimensions")
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
        if args.results_dir:
            expected = [k.strip() for k in args.expect.split(",") if k.strip()]
            results = load_results_dir(args.results_dir, expected)
        else:
            results = load_results(args.results)
    except ValidationFailure as e:
        print(f"validation error: {e}", file=sys.stderr)
        return 2

    config = _load_config(args.config)
    gated_results = apply_suppressions(results, config["suppress"])

    per_dim = {r["audit"]: score_dimension(r, args.total_lines) for r in gated_results}
    overall = overall_score(list(per_dim.values()))
    counts = count_severities(gated_results)
    errored = errored_dimensions(gated_results)

    formats = [f.strip() for f in args.formats.split(",") if f.strip()]

    if "md" in formats:
        Path(args.out).write_text(
            render_markdown(gated_results, per_dim, overall, counts), encoding="utf-8")
    if "sarif" in formats:
        Path(args.sarif_out).write_text(
            json.dumps(to_sarif(gated_results), indent=2), encoding="utf-8")
    if "html" in formats:
        meta = {"project": Path.cwd().name, "date": _dt.date.today().isoformat()}
        if args.discovery:
            disc = json.loads(Path(args.discovery).read_text(encoding="utf-8"))
            meta["project"] = disc.get("project_name", meta["project"])
            meta["languages"] = disc.get("languages", [])
            meta["archetypes"] = disc.get("archetypes", [])
        asset = Path(__file__).parent / "assets" / "chart.umd.min.js"
        chartjs = asset.read_text(encoding="utf-8") if asset.exists() else ""
        Path(args.html_out).write_text(
            render_html(gated_results, per_dim, overall, counts, meta, chartjs),
            encoding="utf-8")

    for r in gated_results:
        if r.get("error"):
            print(f"ERROR: dimension '{r['audit']}' did not run: {r['error']}", file=sys.stderr)

    breaches = evaluate_gate(counts, config["gate"], errored) if args.ci else []
    if breaches:
        for sev, actual, limit in breaches:
            if sev == "Errored-dimension":
                print(f"GATE FAIL: {actual} dimension(s) did not run ({', '.join(errored)}); "
                      "set gate.fail_on_error: false to allow")
            else:
                print(f"GATE FAIL: {sev} findings {actual} exceed limit {limit}")
        return 1
    print(f"Audit report written to {args.out} (overall {overall})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
