SEV_WEIGHTS = {"High": 2.0, "Medium": 0.8, "Low": 0.3, "Info": 0.0}


def dimension_score(findings, total_lines):
    """Display score 0-10 (draft formula). Lower = worse. Rounded to 1 dp."""
    penalty = sum(SEV_WEIGHTS.get(f["severity"], 0.0) for f in findings)
    raw = 10.0 - (penalty / max(total_lines, 1)) * 1000
    return round(max(0.0, min(10.0, raw)), 1)


def is_fully_skipped(checklist):
    """True when a dimension has items and every one is 'skipped' (non-applicable)."""
    return len(checklist) > 0 and all(item["status"] == "skipped" for item in checklist)


def dimension_pass_rate(checklist):
    """Pass rate over APPLICABLE (non-skipped) items only. None if none applicable.

    Consumed by the richer reports in later plans (HTML dashboard pass-rate column);
    kept here as the single source of the applicable-only pass-rate rule (spec 9a.1).
    """
    applicable = [i for i in checklist if i["status"] != "skipped"]
    if not applicable:
        return None
    passed = sum(1 for i in applicable if i["status"] == "pass")
    return round(passed / len(applicable) * 100)


def score_dimension(result, total_lines):
    """Per-dimension score, or None (N/A) when the dimension is fully skipped."""
    if is_fully_skipped(result["checklist"]):
        return None
    return dimension_score(result["findings"], total_lines)


def overall_score(dimension_scores):
    """Average of applicable dimension scores; N/A dims (None) excluded. None if all N/A."""
    applicable = [s for s in dimension_scores if s is not None]
    if not applicable:
        return None
    return round(sum(applicable) / len(applicable), 1)
