# API Reference

The Python package API is the primary integration surface for agents and workflow runners.

All public functions return JSON-compatible dictionaries. The same result payloads are emitted by the CLI as JSON.

Import from `dpawb.api`:

```python
from dpawb.api import assess, coverage, compare, prioritize, summarize
from dpawb.api import capabilities, schema, template, vocabulary
```

## Analytical Operations

### `assess(profile_path: str) -> dict[str, object]`

Assess one composition profile and return an `assessment_result`.

Input:

- `profile_path`: local path to a composition profile YAML file.

The profile may reference local SHACL Turtle files or live URL sources.

### `coverage(profile_path: str, use_case_path: str) -> dict[str, object]`

Assess one use case against one composition profile and return a `coverage_result`.

Inputs:

- `profile_path`: local path to a composition profile YAML file.
- `use_case_path`: local path to one use-case YAML file.

### `compare(left_assessment_path: str, right_assessment_path: str, alignment_path: str | None = None) -> dict[str, object]`

Compare exactly two existing assessment result documents and return a `comparison_result`.

Inputs:

- `left_assessment_path`: local path to the left `assessment_result` JSON document.
- `right_assessment_path`: local path to the right `assessment_result` JSON document.
- `alignment_path`: optional local path to an analyst-authored alignment YAML file.

The two assessment results must have the same declared `comparison_scope_label`.

### `prioritize(assessment_path: str, comparison_path: str | None = None, coverage_paths: list[str] | None = None) -> dict[str, object]`

Rank improvement targets from existing result documents and return a `prioritization_result`.

Inputs:

- `assessment_path`: local path to one `assessment_result` JSON document.
- `comparison_path`: optional local path to one `comparison_result` JSON document.
- `coverage_paths`: optional list of `coverage_result` JSON document paths.

### `summarize(result_paths: list[str]) -> dict[str, object]`

Create a compact deterministic interpretation document from one or more existing result documents.

Input:

- `result_paths`: list of JSON result document paths.

This operation is rule-based. It does not call an AI model.

## Discovery Operations

### `schema(name: str) -> dict[str, object]`

Return a bundled JSON Schema as a `schema_result`.

Common names include:

- `profile`
- `use_case`
- `alignment`
- `assessment_result`
- `coverage_result`
- `comparison_result`
- `prioritization_result`
- `summary_result`

### `vocabulary(name: str) -> dict[str, object]`

Return a bundled controlled vocabulary as a `vocabulary_result`.

Current names:

- `item_categories`
- `join_kinds`

### `template(name: str) -> dict[str, object]`

Return a bundled YAML template as a `template_result`.

Current names:

- `profile`
- `use_case`
- `alignment`

### `capabilities() -> dict[str, object]`

Return a `capabilities_result` describing the package/CLI command surface.

This is the recommended discovery entry point for AI agents and future MCP wrappers.

## Agent Usage Pattern

Agents should treat every API call as a deterministic pipeline step:

1. Prepare explicit YAML or JSON input files.
2. Call one API function.
3. Store the returned dictionary as a JSON result document when it is needed by a downstream step.
4. Pass stored result paths to downstream operations such as `compare`, `prioritize`, or `summarize`.

The API does not perform hidden semantic mapping. Alignment-aware behavior only uses analyst-authored alignment files.
