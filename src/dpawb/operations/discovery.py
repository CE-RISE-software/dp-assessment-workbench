from __future__ import annotations

from dpawb import __version__
from dpawb.resources import load_json_resource, load_yaml_resource


SCHEMAS = {
    "profile": "schemas/profile.schema.json",
    "use_case": "schemas/use_case.schema.json",
    "alignment": "schemas/alignment.schema.json",
    "assessment_result": "schemas/assessment_result.schema.json",
    "coverage_result": "schemas/coverage_result.schema.json",
    "comparison_result": "schemas/comparison_result.schema.json",
    "prioritization_result": "schemas/prioritization_result.schema.json",
}

VOCABULARIES = {
    "item_categories": "vocabularies/item_categories.yaml",
    "join_kinds": "vocabularies/join_kinds.yaml",
}

TEMPLATES = {
    "profile": "templates/profile.yaml",
    "use_case": "templates/use_case.yaml",
    "alignment": "templates/alignment.yaml",
}


def schema(name: str) -> dict[str, object]:
    return {
        "result_type": "schema_result",
        "input_identifiers": {"schema_name": name},
        "artifact_name": name,
        "artifact_kind": "schema",
        "content": load_json_resource(SCHEMAS[name]),
    }


def vocabulary(name: str) -> dict[str, object]:
    return {
        "result_type": "vocabulary_result",
        "input_identifiers": {"vocabulary_name": name},
        "artifact_name": name,
        "artifact_kind": "vocabulary",
        "content": load_yaml_resource(VOCABULARIES[name]),
    }


def template(name: str) -> dict[str, object]:
    return {
        "result_type": "template_result",
        "input_identifiers": {"template_name": name},
        "artifact_name": name,
        "artifact_kind": "template",
        "content": load_yaml_resource(TEMPLATES[name]),
    }


def capabilities() -> dict[str, object]:
    return {
        "result_type": "capabilities_result",
        "input_identifiers": {"tool_name": "dpawb"},
        "tool_version": __version__,
        "commands": [
            {"command": "assess", "inputs": ["profile"], "result_type": "assessment_result"},
            {"command": "coverage", "inputs": ["profile", "use_case"], "result_type": "coverage_result"},
            {
                "command": "compare",
                "inputs": ["left_assessment", "right_assessment", "optional_alignment"],
                "result_type": "comparison_result",
            },
            {
                "command": "prioritize",
                "inputs": ["assessment", "optional_comparison", "optional_coverage_list"],
                "result_type": "prioritization_result",
            },
            {"command": "schema", "inputs": ["name"], "result_type": "schema_result"},
            {"command": "vocabulary", "inputs": ["name"], "result_type": "vocabulary_result"},
            {"command": "template", "inputs": ["name"], "result_type": "template_result"},
            {"command": "capabilities", "inputs": [], "result_type": "capabilities_result"},
        ],
        "schemas": sorted(SCHEMAS),
        "vocabularies": sorted(VOCABULARIES),
        "templates": sorted(TEMPLATES),
    }
