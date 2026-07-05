import json
from pathlib import Path
import jsonschema

_SCHEMA = json.loads((Path(__file__).parent.parent / "shared" / "schema.json").read_text())


class ValidationFailure(Exception):
    """Raised when an AuditResult fails schema validation."""


def load_results(path):
    """Load a JSON array of AuditResult objects and validate each against the schema."""
    data = json.loads(Path(path).read_text())
    if not isinstance(data, list):
        raise ValidationFailure("results file must be a JSON array of AuditResult objects")
    for i, result in enumerate(data):
        try:
            jsonschema.validate(result, _SCHEMA)
        except jsonschema.ValidationError as e:
            raise ValidationFailure(f"result[{i}] ({result.get('audit', '?')}): {e.message}")
    return data
