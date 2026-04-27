#!/usr/bin/env bash
set -eu

export PYTHONPATH="${PYTHONPATH:+$PYTHONPATH:}src"

python -m compileall src tests
python -m unittest discover -s tests -v
python -m dpawb.cli capabilities >/dev/null
python -m dpawb.cli schema composition_recommendation_result >/dev/null
python -m dpawb.cli assess --profile fixtures/profiles/synthetic_evolution_latest.yaml >/dev/null
python -m dpawb.cli coverage \
  --profile fixtures/profiles/synthetic_evolution_latest.yaml \
  --use-case fixtures/use_cases/product_identity_lookup.yaml >/dev/null
python - <<'PY'
from dpawb.mcp_server import McpServer

server = McpServer()
init_response = server.handle_message(
    {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "validate-local", "version": "0.0.0"},
        },
    }
)
assert init_response[0]["result"]["serverInfo"]["name"] == "dpawb-mcp"
tool_response = server.handle_message(
    {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {"name": "capabilities", "arguments": {}},
    }
)
assert tool_response[0]["result"]["structuredContent"]["result_type"] == "capabilities_result"
PY
