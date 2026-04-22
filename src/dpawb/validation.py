from __future__ import annotations

from jsonschema import Draft202012Validator

from dpawb.errors import InputError
from dpawb.resources import load_json_resource


SCHEMA_PATHS = {
    "profile": "schemas/profile.schema.json",
    "use_case": "schemas/use_case.schema.json",
    "alignment": "schemas/alignment.schema.json",
}


def validate_document(document: dict[str, object], schema_name: str, source_label: str) -> None:
    schema = load_json_resource(SCHEMA_PATHS[schema_name])
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(document), key=lambda item: list(item.path))
    if not errors:
        return
    details: list[dict[str, object]] = []
    for error in errors:
        path = ".".join(str(token) for token in error.absolute_path) or "$"
        details.append({"path": path, "message": error.message, "source": source_label})
    raise InputError(
        f"{schema_name} input failed schema validation",
        details=details,
    )
