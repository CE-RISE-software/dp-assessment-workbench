# MCP Readiness

Release `0.1.0` does not ship an MCP server, but the package and CLI are now aligned so a future MCP wrapper can stay thin.

## Alignment Rule

The intended rule is:

- one package API function
- one CLI command
- one future MCP tool

with the same conceptual inputs and the same JSON result payload.

## Current Mapping

| Package API | CLI command | Future MCP tool | Result type |
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

The future MCP server should reuse the same result-envelope style already used by the package:

- `result_type`
- `inputs`
- `content`
- `diagnostics`

This applies to analytical results and now also to discovery-style results.

## Discovery Bridge

`capabilities` is the main bridge for future MCP-aware agent tooling.

It now states, for each operation:

- the CLI command name
- the package API function name
- the intended future MCP tool name
- the conceptual inputs
- stable input-field descriptions
- the emitted result type

That means the future MCP wrapper should not need to invent a second command catalog.

The current package/CLI names remain the source of truth. The `input_fields` entries in `capabilities` are descriptive metadata for future agent tooling and MCP schema generation; they do not introduce a second invocation API.

## Non-Goal For 0.1.0

This repository is not yet committing to:

- an MCP server implementation
- MCP transport/runtime details
- Docker packaging for the MCP wrapper
- MCP registry publication

Those belong after the package contract is considered stable enough to expose directly.
