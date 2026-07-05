"""Convert AuditResult[] to a SARIF 2.1.0 document (GitHub/GitLab code-scanning)."""

_LEVEL = {"High": "error", "Medium": "warning", "Low": "note", "Info": "note"}


def to_sarif(results):
    rules = {}
    sarif_results = []
    for r in results:
        for item in r.get("checklist", []):
            rid = item["id"]
            rules.setdefault(rid, {
                "id": rid,
                "name": item.get("label", rid),
                "shortDescription": {"text": item.get("label", rid)},
            })
        for f in r.get("findings", []):
            rid = f["checklist_id"]
            rules.setdefault(rid, {"id": rid, "name": rid,
                                   "shortDescription": {"text": rid}})
            line = f.get("line")
            physical = {"artifactLocation": {"uri": f["file"]}}
            if isinstance(line, int):
                physical["region"] = {"startLine": line}
            res = {
                "ruleId": rid,
                "level": _LEVEL.get(f.get("severity"), "note"),
                "message": {"text": f.get("title", "")},
                "locations": [{"physicalLocation": physical}],
                "partialFingerprints": {
                    "auditFinding": f"{rid}:{f['file']}:{line}",
                },
                "properties": {
                    "severity": f.get("severity"),
                    "audit": r.get("audit"),
                    "recommendation": f.get("recommendation", ""),
                    "compliance": f.get("compliance_refs", []),
                },
            }
            sarif_results.append(res)
    return {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [{
            "tool": {"driver": {
                "name": "codebase-audit",
                "version": "0.1.0",
                "informationUri": "https://github.com/appuk45/claude-codebase-audit",
                "rules": list(rules.values()),
            }},
            "results": sarif_results,
        }],
    }
