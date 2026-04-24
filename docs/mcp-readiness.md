# MCP Server

Release `0.1.1` ships a thin stdio MCP server over the same deterministic package operations and JSON result contracts.

## Alignment Rule

The implementation rule is:

- one package API function
- one CLI command
- one MCP tool

with the same conceptual inputs and the same JSON result payload.

## Tool Mapping

| Package API | CLI command | MCP tool | Result type |
| --- | --- | --- | --- |
| `assess` | `assess` | `assess` | `assessment_result` |
| `coverage` | `coverage` | `coverage` | `coverage_result` |
| `compare` | `compare` | `compare` | `comparison_result` |
| `prioritize` | `prioritize` | `prioritize` | `prioritization_result` |
| `schema` | `schema` | `schema` | `schema_result` |
| `vocabulary` | `vocabulary` | `vocabulary` | `vocabulary_result` |
| `template` | `template` | `template` | `template_result` |
| `capabilities` | `capabilities` | `capabilities` | `capabilities_result` |
| `summarize` | `summarize` | `summarize` | `summary_result` |

## Result Contract

The MCP server reuses the same result-envelope style already used by the package:

- `result_type`
- `inputs`
- `content`
- `diagnostics`

This applies to analytical results and now also to discovery-style results.

## Discovery Bridge

`capabilities` is the main bridge for MCP-aware agent tooling.

It now states, for each operation:

- the CLI command name
- the package API function name
- the MCP tool name
- the conceptual inputs
- stable input-field descriptions
- the emitted result type

That means the MCP wrapper does not invent a second command catalog.

The current package/CLI names remain the source of truth. The `input_fields` entries in `capabilities` are descriptive metadata for agent tooling and MCP schema generation; they do not introduce a second invocation API.

## Runtime Shape

- local Python entry point: `dpawb-mcp`
- transport: stdio
- message framing: newline-delimited JSON-RPC 2.0
- exposed MCP capability: `tools`
- current tool set: `assess`, `coverage`, `compare`, `prioritize`, `schema`, `vocabulary`, `template`, `capabilities`, `summarize`

## Access And Discovery

The release-`0.1.1` MCP identity is:

- registry name: `io.github.CE-RISE-software/dpawb`
- OCI image pattern: `ghcr.io/ce-rise-software/dpawb-mcp:<release-version>`
- official registry base: `https://registry.modelcontextprotocol.io/`
- source metadata file: `server.json`

Once the GitHub-mirror publication workflow succeeds, the server should be discoverable in the official MCP Registry by searching for `io.github.CE-RISE-software/dpawb`.

Minimal local client configuration:

```json
{
  "mcpServers": {
    "dpawb": {
      "command": "dpawb-mcp"
    }
  }
}
```

## Packaging And Publication

The MCP server is prepared for two runtime paths:

- local Python installation through the `dpawb` package
- GitHub Container Registry image for MCP-oriented distribution from the GitHub mirror

The repository includes placeholder MCP registry metadata in `server.json`. The publish workflow rewrites the release version and OCI image tag at publication time before uploading to the official MCP Registry with GitHub OIDC.

## Non-Goals For 0.1.1

The current MCP release does not add:

- remote HTTP transport
- MCP prompts or resources
- non-deterministic summarization or AI interpretation
- any second analytical contract separate from the package API
