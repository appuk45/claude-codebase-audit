import json
from pathlib import Path

import jsonschema

from engine import DIMENSIONS

_SCHEMA = json.loads((Path(__file__).parent / "schema.json").read_text(encoding="utf-8"))


class ValidationFailure(Exception):
    """Raised when an AuditResult fails schema validation."""


def error_result(audit, message):
    """Placeholder for a dimension that did not produce a valid result."""
    return {"audit": audit, "score": None,
            "iso_characteristic": DIMENSIONS.get(audit, ""),
            "checklist": [], "findings": [], "error": message}


def load_results(path):
    """Load a JSON array of AuditResult objects and validate each against the schema."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValidationFailure("results file must be a JSON array of AuditResult objects")
    for i, result in enumerate(data):
        try:
            jsonschema.validate(result, _SCHEMA)
        except jsonschema.ValidationError as e:
            raise ValidationFailure(f"result[{i}] ({result.get('audit', '?')}): {e.message}")
    return data


def load_results_dir(directory, expected=()):
    """Load one AuditResult per `<audit>.json` file in `directory`.

    Fail-closed by construction: an unreadable/invalid file, or an `expected` dimension
    with no file, becomes an error placeholder instead of silently disappearing. The
    gate (gate.count_errors) then decides whether errors fail the run.
    """
    directory = Path(directory)
    results, seen = [], set()
    for path in sorted(directory.glob("*.json")):
        audit = path.stem
        try:
            result = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(result, list) and len(result) == 1:
                result = result[0]
            jsonschema.validate(result, _SCHEMA)
            audit = result["audit"]
        except (OSError, ValueError, jsonschema.ValidationError) as e:
            msg = e.message if isinstance(e, jsonschema.ValidationError) else str(e)
            result = error_result(audit, f"invalid result file {path.name}: {msg}")
        seen.add(audit)
        results.append(result)
    for audit in expected:
        if audit not in seen:
            results.append(error_result(audit, "no result produced (dimension failed or was not run)"))
    return results
