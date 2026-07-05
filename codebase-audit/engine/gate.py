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


def evaluate_gate(counts, gate_cfg):
    """Return a list of (severity, actual, limit) breaches. Empty list = gate passes.

    A gate limit of None means 'ignore that severity'.
    """
    breaches = []
    for sev, key in _GATE_KEYS:
        limit = gate_cfg.get(key)
        if limit is not None and counts[sev] > limit:
            breaches.append((sev, counts[sev], limit))
    return breaches
