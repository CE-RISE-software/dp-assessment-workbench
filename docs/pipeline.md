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

- `recommend-composition`
  Input: two `assessment_result` documents, optional `comparison_result`, and optional list of `coverage_result` documents
  Output: one `composition_recommendation_result`
  Produces a deterministic combined-profile recommendation with module inclusion and entity deduplication review items.
  The result is a decision-support artifact: it proposes how to combine already assessed model sets, but it does not generate or merge SHACL files.

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

For `composition_recommendation_result`, the main sections are:

- `candidate_profile`
  A proposed composition profile made from selected modules in the assessed inputs.
- `module_recommendations`
  Include decisions for modules from the left and right model sets.
- `entity_recommendations`
  Alignment-based decisions for duplicated or unique declared equivalent entities.
- `review_items`
  Human or agent review points that should be inspected before implementing a combined model.

Current release-1 analytical semantics are intentionally conservative, but they now include:

- direct contradiction detection for cardinality conflicts and datatype-versus-object-reference conflicts
- item coverage matching from SHACL property-path, owner-shape, and target-class evidence
- join coverage matching from shared owner shapes, explicit cross-shape object-reference paths, or record-level retrieval context where appropriate
- composition recommendation from existing assessment, comparison, and coverage result documents

## Discovery

The tool exposes built-in artifacts through:

- `schema`
- `vocabulary`
- `template`
- `capabilities`

These discovery commands are intended for both humans and AI-agent skills.
