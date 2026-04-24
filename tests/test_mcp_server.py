from __future__ import annotations

import json
import unittest
from pathlib import Path

from dpawb.mcp_server import McpServer


class McpServerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.server = McpServer()

    def _initialize(self) -> None:
        responses = self.server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {"name": "test-client", "version": "0.0.0"},
                },
            }
        )
        self.assertEqual(responses[0]["result"]["capabilities"]["tools"]["listChanged"], False)
        self.server.handle_message({"jsonrpc": "2.0", "method": "notifications/initialized"})

    def test_initialize_returns_tools_capability(self) -> None:
        responses = self.server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": "init-1",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {"name": "test-client", "version": "0.0.0"},
                },
            }
        )
        result = responses[0]["result"]
        self.assertEqual(result["protocolVersion"], "2025-06-18")
        self.assertEqual(result["serverInfo"]["name"], "dpawb-mcp")

    def test_tools_list_returns_expected_contract_surface(self) -> None:
        self._initialize()
        responses = self.server.handle_message({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        tools = responses[0]["result"]["tools"]
        names = [tool["name"] for tool in tools]
        self.assertIn("assess", names)
        self.assertIn("summarize", names)

    def test_tools_call_returns_structured_result(self) -> None:
        self._initialize()
        responses = self.server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "capabilities",
                    "arguments": {},
                },
            }
        )
        result = responses[0]["result"]
        self.assertEqual(result["isError"], False)
        self.assertEqual(result["structuredContent"]["result_type"], "capabilities_result")

    def test_tool_errors_are_returned_as_tool_results(self) -> None:
        self._initialize()
        responses = self.server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {
                    "name": "assess",
                    "arguments": {"profile": "does-not-exist.yaml"},
                },
            }
        )
        result = responses[0]["result"]
        self.assertEqual(result["isError"], True)
        self.assertEqual(result["structuredContent"]["result_type"], "error_result")

    def test_requests_before_initialize_are_rejected(self) -> None:
        responses = self.server.handle_message({"jsonrpc": "2.0", "id": 5, "method": "tools/list"})
        self.assertEqual(responses[0]["error"]["code"], -32600)

    def test_server_json_matches_release_identity(self) -> None:
        server_document = json.loads(Path("server.json").read_text(encoding="utf-8"))
        self.assertEqual(server_document["name"], "io.github.CE-RISE-software/dpawb")
        self.assertEqual(server_document["version"], "0.0.0")
        self.assertEqual(server_document["packages"][0]["identifier"], "ghcr.io/ce-rise-software/dpawb-mcp:0.0.0")
