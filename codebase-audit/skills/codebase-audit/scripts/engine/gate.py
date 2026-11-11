import copy

_SEVERITIES = ["High", "Medium", "Low", "Info"]
_GATE_KEYS = [("High", "max_high"), ("Medium", "max_medium"), ("Low", "max_low")]


def count_severities(results):
    counts = {s: 0 for s in _SEVERITIES}
    for r in results:
        for f in r.get("findings", []):
            sev = f.get("severity")
            if sev in counts:
                counts[sev] += 1
    return counts


def errored_dimensions(results):
    """Audit keys of dimensions that failed to produce a valid result."""
    return [r.get("audit", "?") for r in results if r.get("error")]


def apply_suppressions(results, suppressions):
    """Remove findings whose 'checklist_id@file' is in the suppression list. Non-mutating."""
    supp = set(suppressions or [])
    out = copy.deepcopy(results)
    for r in out:
        r["findings"] = [
            f for f in r.get("findings", [])
            if f"{f.get('checklist_id')}@{f.get('file')}" not in supp
        ]
    return out


def evaluate_gate(counts, gate_cfg, errored=()):
    """Return a list of (severity, actual, limit) breaches. Empty list = gate passes.

    A gate limit of None means 'ignore that severity'. Errored dimensions fail the gate
    unless `fail_on_error` is explicitly false: a dimension that never ran reports zero
    findings, so passing it would be fail-open.
    """
    breaches = []
    for sev, key in _GATE_KEYS:
        limit = gate_cfg.get(key)
        if limit is not None and counts[sev] > limit:
            breaches.append((sev, counts[sev], limit))
    if errored and gate_cfg.get("fail_on_error", True):
        breaches.append(("Errored-dimension", len(errored), 0))
    return breaches
