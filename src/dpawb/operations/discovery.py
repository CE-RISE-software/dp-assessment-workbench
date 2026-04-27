from __future__ import annotations

from dpawb import __version__
from dpawb.result import build_result
from dpawb.resources import load_json_resource, load_yaml_resource


SCHEMAS = {
    "profile": "schemas/profile.schema.json",
    "use_case": "schemas/use_case.schema.json",
    "alignment": "schemas/alignment.schema.json",
    "assessment_result": "schemas/assessment_result.schema.json",
    "coverage_result": "schemas/coverage_result.schema.json",
    "comparison_result": "schemas/comparison_result.schema.json",
    "prioritization_result": "schemas/prioritization_result.schema.json",
    "composition_recommendation_result": "schemas/composition_recommendation_result.schema.json",
    "summary_result": "schemas/summary_result.schema.json",
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
    return build_result(
        "schema_result",
        {"name": name},
        {
            "artifact_name": name,
            "artifact_kind": "schema",
            "document": load_json_resource(SCHEMAS[name]),
        },
        [],
    )


def vocabulary(name: str) -> dict[str, object]:
    return build_result(
        "vocabulary_result",
        {"name": name},
        {
            "artifact_name": name,
            "artifact_kind": "vocabulary",
            "document": load_yaml_resource(VOCABULARIES[name]),
        },
        [],
    )


def template(name: str) -> dict[str, object]:
    return build_result(
        "template_result",
        {"name": name},
        {
            "artifact_name": name,
            "artifact_kind": "template",
            "document": load_yaml_resource(TEMPLATES[name]),
        },
        [],
    )


def capabilities() -> dict[str, object]:
    return build_result(
        "capabilities_result",
        {"tool_name": "dpawb"},
        {
            "tool_version": __version__,
            "commands": [
                {
                    "command": "assess",
                    "api_function": "assess",
                    "mcp_tool": "assess",
                    "inputs": ["profile"],
                    "input_fields": {"profile": "Path or URL-backed composition profile YAML."},
                    "result_type": "assessment_result",
                },
                {
                    "command": "coverage",
                    "api_function": "coverage",
                    "mcp_tool": "coverage",
                    "inputs": ["profile", "use_case"],
                    "input_fields": {
                        "profile": "Path or URL-backed composition profile YAML.",
                        "use_case": "Path to one use-case YAML file.",
                    },
                    "result_type": "coverage_result",
                },
                {
                    "command": "compare",
                    "api_function": "compare",
                    "mcp_tool": "compare",
                    "inputs": ["left_assessment", "right_assessment", "optional_alignment"],
                    "input_fields": {
                        "left_assessment": "Path to the left assessment_result JSON document.",
                        "right_assessment": "Path to the right assessment_result JSON document.",
                        "alignment": "Optional path to an analyst-authored alignment YAML file.",
                    },
                    "result_type": "comparison_result",
                },
                {
                    "command": "prioritize",
                    "api_function": "prioritize",
                    "mcp_tool": "prioritize",
                    "inputs": ["assessment", "optional_comparison", "optional_coverage_list"],
                    "input_fields": {
                        "assessment": "Path to one assessment_result JSON document.",
                        "comparison": "Optional path to one comparison_result JSON document.",
                        "coverage": "Optional list of coverage_result JSON document paths.",
                    },
                    "result_type": "prioritization_result",
                },
                {
                    "command": "recommend-composition",
                    "api_function": "recommend_composition",
                    "mcp_tool": "recommend_composition",
                    "inputs": ["left_assessment", "right_assessment", "optional_comparison", "optional_coverage_list"],
                    "input_fields": {
                        "left_assessment": "Path to the left assessment_result JSON document.",
                        "right_assessment": "Path to the right assessment_result JSON document.",
                        "comparison": "Optional path to one comparison_result JSON document.",
                        "coverage": "Optional list of coverage_result JSON document paths.",
                    },
                    "result_type": "composition_recommendation_result",
                },
                {
                    "command": "schema",
                    "api_function": "schema",
                    "mcp_tool": "schema",
                    "inputs": ["name"],
                    "input_fields": {"name": "Built-in schema name."},
                    "result_type": "schema_result",
                },
                {
                    "command": "vocabulary",
                    "api_function": "vocabulary",
                    "mcp_tool": "vocabulary",
                    "inputs": ["name"],
                    "input_fields": {"name": "Built-in vocabulary name."},
                    "result_type": "vocabulary_result",
                },
                {
                    "command": "template",
                    "api_function": "template",
                    "mcp_tool": "template",
                    "inputs": ["name"],
                    "input_fields": {"name": "Built-in template name."},
                    "result_type": "template_result",
                },
                {
                    "command": "capabilities",
                    "api_function": "capabilities",
                    "mcp_tool": "capabilities",
                    "inputs": [],
                    "input_fields": {},
                    "result_type": "capabilities_result",
                },
                {
                    "command": "summarize",
                    "api_function": "summarize",
                    "mcp_tool": "summarize",
                    "inputs": ["result_list"],
                    "input_fields": {
                        "result": "One or more existing result JSON document paths.",
                    },
                    "result_type": "summary_result",
                },
            ],
            "schemas": sorted(SCHEMAS),
            "vocabularies": sorted(VOCABULARIES),
            "templates": sorted(TEMPLATES),
        },
        [],
    )
