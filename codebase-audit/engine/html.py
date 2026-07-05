"""Render a self-contained HTML dashboard from audit data."""

import html as _html
import json

_SEV_COLOR = {"High": "#ef4444", "Medium": "#f97316", "Low": "#eab308", "Info": "#3b82f6"}
_STATUS_ICON = {"pass": "✅", "fail": "❌", "warning": "⚠️",
                "skipped": "⏭️"}


def _score_str(s):
    return "N/A" if s is None else f"{s}/10"


def _esc(x):
    return _html.escape(str(x))


def _cards(results, per_dim):
    out = []
    for r in results:
        name = r["audit"]
        out.append(
            f'<div class="card"><div class="dim">{_esc(name)}</div>'
            f'<div class="iso">{_esc(r.get("iso_characteristic", ""))}</div>'
            f'<div class="score">{_score_str(per_dim.get(name))}</div></div>'
        )
    return "".join(out)


def _sections(results, per_dim):
    out = []
    for r in results:
        name = r["audit"]
        chk = "".join(
            f'<li>{_STATUS_ICON.get(i["status"], _STATUS_ICON["warning"])} '
            f'{_esc(i.get("label", i["id"]))}</li>'
            for i in r.get("checklist", [])
        )
        rows = ""
        for f in r.get("findings", []):
            refs = ", ".join(_esc(c) for c in f.get("compliance_refs", []))
            color = _SEV_COLOR.get(f.get("severity"), "#888")
            loc = f'{_esc(f["file"])}:{_esc(f.get("line", "—"))}'
            rows += (
                f'<tr><td style="color:{color};font-weight:700">{_esc(f.get("severity"))}</td>'
                f'<td class="mono">{loc}</td><td>{_esc(f.get("title", ""))}</td>'
                f'<td>{refs}</td><td>{_esc(f.get("recommendation", ""))}</td></tr>'
            )
        if not rows:
            rows = '<tr><td colspan="5" class="muted">No findings</td></tr>'
        out.append(
            f'<section><h2>{_esc(name)} — {_score_str(per_dim.get(name))}</h2>'
            f'<ul class="chk">{chk}</ul>'
            f'<table><thead><tr><th>Severity</th><th>File:Line</th><th>Issue</th>'
            f'<th>Compliance</th><th>Recommendation</th></tr></thead>'
            f'<tbody>{rows}</tbody></table></section>'
        )
    return "".join(out)


def render_html(results, per_dim_scores, overall, counts, meta, chartjs_source=""):
    project = _esc(meta.get("project", "project"))
    date = _esc(meta.get("date", ""))
    data_js = json.dumps({
        "labels": [r["audit"] for r in results],
        "scores": [per_dim_scores.get(r["audit"]) or 0 for r in results],
    })
    chart_block = ""
    if chartjs_source:
        chart_block = (
            '<canvas id="radar" height="110"></canvas>'
            f'<script>{chartjs_source}</script>'
            f'<script>const D={data_js};new Chart(document.getElementById("radar"),'
            '{type:"radar",data:{labels:D.labels,datasets:[{data:D.scores,'
            'backgroundColor:"rgba(99,102,241,.15)",borderColor:"#6366f1",borderWidth:2}]},'
            'options:{scales:{r:{min:0,max:10,grid:{color:"#334155"},'
            'angleLines:{color:"#334155"},pointLabels:{color:"#94a3b8"}}},'
            'plugins:{legend:{display:false}}}});</script>'
        )
    return (
        "<!DOCTYPE html>\n<html lang=\"en\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
        f"<title>Codebase Audit — {project} — {date}</title><style>"
        "body{font-family:system-ui,-apple-system,sans-serif;background:#0f172a;"
        "color:#e2e8f0;margin:0;padding:24px}"
        ".cards{display:flex;flex-wrap:wrap;gap:12px;margin:16px 0}"
        ".card{background:#1e293b;border:1px solid #334155;border-radius:10px;"
        "padding:14px;min-width:150px}"
        ".dim{font-weight:600;text-transform:capitalize}.iso{font-size:11px;color:#94a3b8}"
        ".score{font-size:28px;font-weight:800;margin-top:6px}"
        "section{background:#1e293b;border:1px solid #334155;border-radius:10px;"
        "padding:16px;margin:16px 0}"
        "table{width:100%;border-collapse:collapse;font-size:13px}"
        "th,td{text-align:left;padding:6px 10px;border-bottom:1px solid #334155;"
        "vertical-align:top}"
        "th{color:#94a3b8;font-size:11px;text-transform:uppercase}"
        ".mono{font-family:monospace;color:#a5b4fc}.muted{color:#94a3b8}"
        ".chk{list-style:none;padding:0;columns:2;font-size:13px}"
        "h1{margin:.2em 0;text-transform:capitalize}h2{margin:.2em 0;text-transform:capitalize}"
        ".summary{font-size:15px;margin-bottom:8px}"
        "</style></head><body>"
        f"<h1>{project}</h1>"
        f'<div class="summary">\U0001f4c5 {date} &nbsp; Overall: '
        f"<b>{_score_str(overall)}</b> &nbsp; "
        f"{counts['High']}H {counts['Medium']}M {counts['Low']}L {counts['Info']}I</div>"
        f"{chart_block}"
        f'<div class="cards">{_cards(results, per_dim_scores)}</div>'
        f"{_sections(results, per_dim_scores)}"
        "</body></html>"
    )
