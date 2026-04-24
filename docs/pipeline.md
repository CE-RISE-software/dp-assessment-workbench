# Pipeline

The release-1 analytical pipeline is intentionally explicit and file-based.

## Operations

- `assess`
  Input: one composition profile
  Output: one `assessment_result`

- `coverage`
  Input: one composition profile and one use-case file
  Output: one `coverage_result`

- `compare`
  Input: two `assessment_result` documents and optional alignment file
  Output: one `comparison_result`

- `prioritize`
  Input: one `assessment_result`, optional `comparison_result`, and optional list of `coverage_result` documents
  Output: one `prioritization_result`
  Consumes coverage gaps, maintainability findings, structural comparison observations, and alignment-gap observations when present.

- `summarize`
  Input: one or more result documents
  Output: one `summary_result`
  Produces a compact deterministic interpretation over existing results without rerunning analysis.
  The JSON result is canonical; the CLI may also render it as Markdown.

## Result Documents

All analytical result documents use the same top-level envelope:

- `result_type`
- `inputs`
- `content`
- `diagnostics`

For `comparison_result`, the main analytical sections are:

- `structural_comparison`
  Metric deltas and ranked structural observations.

- `alignment`
  Present only when an alignment file is supplied.
  Includes aggregate counts, `evaluated_pairs`, and `ranked_alignment_observations` for unmatched declared equivalences.

For `prioritization_result`, the ranked target list may therefore include:

- coverage gaps
- maintainability findings
- structural comparison observations
- alignment gaps derived from declared but incompletely matched equivalences

For `summary_result`, the main sections are:

- `headline`
- `result_types`
- `key_points`
- `follow_up_questions`

Current release-1 analytical semantics are intentionally conservative, but they now include:

- direct contradiction detection for cardinality conflicts and datatype-versus-object-reference conflicts
- item coverage matching from SHACL property-path, owner-shape, and target-class evidence
- join coverage matching from shared owner shapes, explicit cross-shape object-reference paths, or record-level retrieval context where appropriate

## Discovery

The tool exposes built-in artifacts through:

- `schema`
- `vocabulary`
- `template`
- `capabilities`

These discovery commands are intended for both humans and AI-agent skills.
