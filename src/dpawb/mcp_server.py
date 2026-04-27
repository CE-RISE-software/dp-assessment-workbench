from __future__ import annotations

import json
import sys
from collections.abc import Callable
from typing import Any

from dpawb import __version__
from dpawb.api import (
    assess,
    capabilities,
    compare,
    coverage,
    prioritize,
    recommend_composition,
    schema,
    summarize,
    template,
    vocabulary,
)
from dpawb.errors import DpawbError, InputError
from dpawb.io import dump_json

SUPPORTED_PROTOCOL_VERSIONS = (
    "2024-11-05",
    "2025-03-26",
    "2025-06-18",
    "2025-11-25",
)
LATEST_PROTOCOL_VERSION = SUPPORTED_PROTOCOL_VERSIONS[-1]

JSONRPC_INVALID_REQUEST = -32600
JSONRPC_METHOD_NOT_FOUND = -32601
JSONRPC_INVALID_PARAMS = -32602


def _tool_input_schema(properties: dict[str, dict[str, object]], required: list[str]) -> dict[str, object]:
    return {
        "type": "object",
        "properties": properties,
        "required": required,
        "additionalProperties": False,
    }


TOOL_DEFINITIONS = [
    {
        "name": "assess",
        "title": "Assess Profile",
        "description": "Assess one composition profile and return one assessment_result document.",
        "inputSchema": _tool_input_schema(
            {
                "profile": {
                    "type": "string",
                    "description": "Local path to one composition profile YAML file.",
                }
            },
            ["profile"],
        ),
    },
    {
        "name": "coverage",
        "title": "Assess Use-Case Coverage",
        "description": "Assess one use case against one composition profile and return one coverage_result document.",
        "inputSchema": _tool_input_schema(
            {
                "profile": {
                    "type": "string",
                    "description": "Local path to one composition profile YAML file.",
                },
                "use_case": {
                    "type": "string",
                    "description": "Local path to one use-case YAML file.",
                },
            },
            ["profile", "use_case"],
        ),
    },
    {
        "name": "compare",
        "title": "Compare Assessments",
        "description": "Compare exactly two assessment_result documents and optionally apply an analyst-authored alignment file.",
        "inputSchema": _tool_input_schema(
            {
                "left_assessment": {
                    "type": "string",
                    "description": "Local path to the left assessment_result JSON document.",
                },
                "right_assessment": {
                    "type": "string",
                    "description": "Local path to the right assessment_result JSON document.",
                },
                "alignment": {
                    "type": "string",
                    "description": "Optional local path to one alignment YAML file.",
                },
            },
            ["left_assessment", "right_assessment"],
        ),
    },
    {
        "name": "prioritize",
        "title": "Prioritize Improvement Targets",
        "description": "Rank improvement targets from one assessment_result document plus optional downstream result documents.",
        "inputSchema": _tool_input_schema(
            {
                "assessment": {
                    "type": "string",
                    "description": "Local path to one assessment_result JSON document.",
                },
                "comparison": {
                    "type": "string",
                    "description": "Optional local path to one comparison_result JSON document.",
                },
                "coverage": {
                    "type": "array",
                    "description": "Optional list of local coverage_result JSON document paths.",
                    "items": {"type": "string"},
                },
            },
            ["assessment"],
        ),
    },
    {
        "name": "recommend_composition",
        "title": "Recommend Composition",
        "description": "Recommend a deterministic combined composition from two assessment results.",
        "inputSchema": _tool_input_schema(
            {
                "left_assessment": {
                    "type": "string",
                    "description": "Local path to the left assessment_result JSON document.",
                },
                "right_assessment": {
                    "type": "string",
                    "description": "Local path to the right assessment_result JSON document.",
                },
                "comparison": {
                    "type": "string",
                    "description": "Optional local path to one comparison_result JSON document.",
                },
                "coverage": {
                    "type": "array",
                    "description": "Optional list of local coverage_result JSON document paths.",
                    "items": {"type": "string"},
                },
            },
            ["left_assessment", "right_assessment"],
        ),
    },
    {
        "name": "schema",
        "title": "Get Schema",
        "description": "Return one bundled JSON Schema.",
        "inputSchema": _tool_input_schema(
            {
                "name": {
                    "type": "string",
                    "enum": [
                        "profile",
                        "use_case",
                        "alignment",
                        "assessment_result",
                        "coverage_result",
                        "comparison_result",
                        "prioritization_result",
                        "composition_recommendation_result",
                        "summary_result",
                    ],
                }
            },
            ["name"],
        ),
    },
    {
        "name": "vocabulary",
        "title": "Get Vocabulary",
        "description": "Return one bundled controlled vocabulary document.",
        "inputSchema": _tool_input_schema(
            {
                "name": {
                    "type": "string",
                    "enum": ["item_categories", "join_kinds"],
                }
            },
            ["name"],
        ),
    },
    {
        "name": "template",
        "title": "Get Template",
        "description": "Return one bundled YAML template document.",
        "inputSchema": _tool_input_schema(
            {
                "name": {
                    "type": "string",
                    "enum": ["profile", "use_case", "alignment"],
                }
            },
            ["name"],
        ),
    },
    {
        "name": "capabilities",
        "title": "Get Capabilities",
        "description": "Return the deterministic command and artifact capability catalog.",
        "inputSchema": _tool_input_schema({}, []),
    },
    {
        "name": "summarize",
        "title": "Summarize Results",
        "description": "Create one deterministic summary_result document from one or more existing result JSON documents.",
        "inputSchema": _tool_input_schema(
            {
                "result": {
                    "type": "array",
                    "description": "One or more local paths to result JSON documents.",
                    "items": {"type": "string"},
                    "minItems": 1,
                }
            },
            ["result"],
        ),
    },
]


class McpServer:
    """Thin stdio MCP server exposing the public dpawb operations as tools."""

    def __init__(self) -> None:
        self._has_initialized = False
        self._protocol_version = LATEST_PROTOCOL_VERSION
        self._tool_handlers: dict[str, Callable[[dict[str, object]], dict[str, object]]] = {
            "assess": self._call_assess,
            "coverage": self._call_coverage,
            "compare": self._call_compare,
            "prioritize": self._call_prioritize,
            "recommend_composition": self._call_recommend_composition,
            "schema": self._call_schema,
            "vocabulary": self._call_vocabulary,
            "template": self._call_template,
            "capabilities": self._call_capabilities,
            "summarize": self._call_summarize,
        }

    def handle_message(self, payload: Any) -> list[dict[str, object]]:
        """Process one JSON-RPC message or batch and return any responses."""

        if isinstance(payload, list):
            responses: list[dict[str, object]] = []
            for item in payload:
                responses.extend(self.handle_message(item))
            return responses
        if not isinstance(payload, dict):
            return [self._error_response(None, JSONRPC_INVALID_REQUEST, "Request must be a JSON object.")]
        if "method" not in payload:
            return []

        method = payload["method"]
        request_id = payload.get("id")
        params = payload.get("params", {})
        if params is None:
            params = {}
        if not isinstance(params, dict):
            return [self._error_response(request_id, JSONRPC_INVALID_PARAMS, "Request params must be an object.")]

        if method == "initialize":
            return [self._handle_initialize(request_id, params)]
        if method == "notifications/initialized":
            return []
        if method == "ping":
            return [self._response(request_id, {})]
        if method == "tools/list":
            return [self._handle_tools_list(request_id)]
        if method == "tools/call":
            return [self._handle_tools_call(request_id, params)]
        return [self._error_response(request_id, JSONRPC_METHOD_NOT_FOUND, f"Unsupported method: {method}")]

    def _handle_initialize(self, request_id: object, params: dict[str, object]) -> dict[str, object]:
        if request_id is None:
            return self._error_response(None, JSONRPC_INVALID_REQUEST, "initialize must be a request.")
        requested_version = params.get("protocolVersion")
        if isinstance(requested_version, str) and requested_version in SUPPORTED_PROTOCOL_VERSIONS:
            self._protocol_version = requested_version
        else:
            self._protocol_version = LATEST_PROTOCOL_VERSION
        self._has_initialized = True
        return self._response(
            request_id,
            {
                "protocolVersion": self._protocol_version,
                "capabilities": {
                    "tools": {
                        "listChanged": False,
                    }
                },
                "serverInfo": {
                    "name": "dpawb-mcp",
                    "title": "Digital Passport Assessment Workbench MCP Server",
                    "version": __version__,
                },
                "instructions": (
                    "Use the deterministic dpawb analytical tools over explicit file-based inputs. "
                    "All tool calls return the canonical JSON result documents in structuredContent."
                ),
            },
        )

    def _handle_tools_list(self, request_id: object) -> dict[str, object]:
        error = self._require_initialized(request_id)
        if error:
            return error
        return self._response(request_id, {"tools": TOOL_DEFINITIONS})

    def _handle_tools_call(self, request_id: object, params: dict[str, object]) -> dict[str, object]:
        error = self._require_initialized(request_id)
        if error:
            return error
        name = params.get("name")
        arguments = params.get("arguments", {})
        if not isinstance(name, str):
            return self._error_response(request_id, JSONRPC_INVALID_PARAMS, "Tool name must be a string.")
        if not isinstance(arguments, dict):
            return self._error_response(request_id, JSONRPC_INVALID_PARAMS, "Tool arguments must be an object.")
        handler = self._tool_handlers.get(name)
        if handler is None:
            return self._error_response(request_id, JSONRPC_METHOD_NOT_FOUND, f"Unknown tool: {name}")
        try:
            result = handler(arguments)
            return self._response(request_id, self._tool_result(result, is_error=False))
        except DpawbError as exc:
            error_result = exc.to_result()
            return self._response(request_id, self._tool_result(error_result, is_error=True))
        except Exception as exc:  # pragma: no cover
            error_result = {
                "result_type": "error_result",
                "error": {
                    "code": "internal_error",
                    "message": str(exc),
                    "details": [],
                },
            }
            return self._response(request_id, self._tool_result(error_result, is_error=True))

    def _require_initialized(self, request_id: object) -> dict[str, object] | None:
        if self._has_initialized:
            return None
        return self._error_response(
            request_id,
            JSONRPC_INVALID_REQUEST,
            "The client must send initialize before calling other MCP methods.",
        )

    def _call_assess(self, arguments: dict[str, object]) -> dict[str, object]:
        return assess(self._require_string(arguments, "profile"))

    def _call_coverage(self, arguments: dict[str, object]) -> dict[str, object]:
        return coverage(self._require_string(arguments, "profile"), self._require_string(arguments, "use_case"))

    def _call_compare(self, arguments: dict[str, object]) -> dict[str, object]:
        alignment = arguments.get("alignment")
        if alignment is not None and not isinstance(alignment, str):
            raise InputError("Tool argument 'alignment' must be a string when provided.")
        return compare(
            self._require_string(arguments, "left_assessment"),
            self._require_string(arguments, "right_assessment"),
            alignment,
        )

    def _call_prioritize(self, arguments: dict[str, object]) -> dict[str, object]:
        comparison = arguments.get("comparison")
        if comparison is not None and not isinstance(comparison, str):
            raise InputError("Tool argument 'comparison' must be a string when provided.")
        coverage_paths = arguments.get("coverage")
        if coverage_paths is None:
            coverage_list: list[str] = []
        elif isinstance(coverage_paths, list) and all(isinstance(item, str) for item in coverage_paths):
            coverage_list = coverage_paths
        else:
            raise InputError("Tool argument 'coverage' must be a list of strings when provided.")
        return prioritize(self._require_string(arguments, "assessment"), comparison, coverage_list)

    def _call_recommend_composition(self, arguments: dict[str, object]) -> dict[str, object]:
        comparison = arguments.get("comparison")
        if comparison is not None and not isinstance(comparison, str):
            raise InputError("Tool argument 'comparison' must be a string when provided.")
        coverage_paths = arguments.get("coverage")
        if coverage_paths is None:
            coverage_list: list[str] = []
        elif isinstance(coverage_paths, list) and all(isinstance(item, str) for item in coverage_paths):
            coverage_list = coverage_paths
        else:
            raise InputError("Tool argument 'coverage' must be a list of strings when provided.")
        return recommend_composition(
            self._require_string(arguments, "left_assessment"),
            self._require_string(arguments, "right_assessment"),
            comparison,
            coverage_list,
        )

    def _call_schema(self, arguments: dict[str, object]) -> dict[str, object]:
        return schema(self._require_string(arguments, "name"))

    def _call_vocabulary(self, arguments: dict[str, object]) -> dict[str, object]:
        return vocabulary(self._require_string(arguments, "name"))

    def _call_template(self, arguments: dict[str, object]) -> dict[str, object]:
        return template(self._require_string(arguments, "name"))

    def _call_capabilities(self, arguments: dict[str, object]) -> dict[str, object]:
        if arguments:
            raise InputError("The capabilities tool does not accept arguments.")
        return capabilities()

    def _call_summarize(self, arguments: dict[str, object]) -> dict[str, object]:
        paths = arguments.get("result")
        if not isinstance(paths, list) or not paths or not all(isinstance(item, str) for item in paths):
            raise InputError("Tool argument 'result' must be a non-empty list of strings.")
        return summarize(paths)

    def _require_string(self, arguments: dict[str, object], name: str) -> str:
        value = arguments.get(name)
        if not isinstance(value, str):
            raise InputError(f"Tool argument '{name}' must be a string.")
        return value

    def _tool_result(self, result: dict[str, object], is_error: bool) -> dict[str, object]:
        return {
            "content": [
                {
                    "type": "text",
                    "text": dump_json(result).rstrip(),
                }
            ],
            "structuredContent": result,
            "isError": is_error,
        }

    def _response(self, request_id: object, result: dict[str, object]) -> dict[str, object]:
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result,
        }

    def _error_response(self, request_id: object, code: int, message: str) -> dict[str, object]:
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": code,
                "message": message,
            },
        }


def run_stdio_server() -> int:
    """Run the stdio MCP server until EOF."""

    server = McpServer()
    for raw_line in sys.stdin:
        line = raw_line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            response = server._error_response(None, JSONRPC_INVALID_REQUEST, "Input line is not valid JSON.")
            sys.stdout.write(json.dumps(response, separators=(",", ":")) + "\n")
            sys.stdout.flush()
            continue
        for response in server.handle_message(payload):
            sys.stdout.write(json.dumps(response, separators=(",", ":")) + "\n")
            sys.stdout.flush()
    return 0


def main() -> int:
    """Entry point for the stdio MCP server."""

    return run_stdio_server()


if __name__ == "__main__":
    raise SystemExit(main())
