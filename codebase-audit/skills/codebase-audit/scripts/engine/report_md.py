from engine.scoring import score_label


def _fmt_score(s):
    return "N/A" if s is None else f"{s}/10"


def render_markdown(results, per_dim_scores, overall, counts):
    """Render a diff-friendly markdown report for CI logs / PR comments."""
    lines = []
    lines.append("# Codebase Audit Report")
    lines.append("")
    lines.append(f"**Overall score:** {_fmt_score(overall)}")
    lines.append("")
    lines.append(
        f"**Findings:** {counts['High']} High · {counts['Medium']} Medium · "
        f"{counts['Low']} Low · {counts['Info']} Info"
    )
    lines.append("")
    lines.append("## Dimension Scores")
    lines.append("")
    lines.append("| Dimension | ISO | Score |")
    lines.append("|---|---|---|")
    for r in results:
        name = r["audit"]
        lines.append(f"| {name} | {r.get('iso_characteristic', '')} | "
                     f"{score_label(r, per_dim_scores.get(name))} |")
    lines.append("")
    errored = [r for r in results if r.get("error")]
    if errored:
        lines.append("## Dimensions that did not run")
        lines.append("")
        for r in errored:
            lines.append(f"- **{r['audit']}** — {r['error']}")
        lines.append("")
    lines.append("## Findings")
    lines.append("")
    any_findings = False
    for r in results:
        for f in r.get("findings", []):
            any_findings = True
            loc = f"{f['file']}:{f.get('line', '—')}"
            lines.append(
                f"- **[{f['severity']}]** `{loc}` — {f['title']} "
                f"({r['audit']}). _{f.get('recommendation', '')}_"
            )
    if not any_findings:
        lines.append("_No findings._")
    lines.append("")
    return "\n".join(lines)
