# Result Interpretation

The workbench produces rich JSON outputs.

This is intentional. The raw outputs are meant to be:

- inspectable by humans
- parseable by AI agents
- suitable for reproducible pipelines
- traceable back to model inputs

## Result Envelope

All current result documents use the same top-level envelope:

- `result_type`
- `inputs`
- `content`
- `diagnostics`

`inputs` identifies what was analyzed.

`content` contains the operation-specific analytical result.

`diagnostics` records non-fatal notes, limitations, or processing details.

## Reading Assessment Results

An `assessment_result` should be read as a model instrument panel.

The main sections are:

- metrics
- maintainability findings
- module summaries
- trace index

The metrics show model size, explicitness, constraint readiness, and interoperability signals.

Maintainability findings should be inspected as candidate issues, not automatically as defects.

## Reading Coverage Results

A `coverage_result` answers whether a declared use case is representable from the composed SHACL model.

Important fields are:

- `overall_coverage_class`
- `required_item_findings`
- `required_join_findings`
- `supporting_trace`

`supporting_trace` is important because it shows why the workbench classified an item or join in a certain way.

## Reading Comparison Results

A `comparison_result` compares exactly two assessment results.

Important sections are:

- `metric_deltas`
- `ranked_observations`
- optional `alignment`

`ranked_observations` are sorted to emphasize normalized analytical signals before raw size differences.

When an alignment file is provided, inspect:

- `alignment_coverage_ratio`
- `evaluated_pairs`
- `ranked_alignment_observations`

Alignment results are declaration-based. The workbench does not infer semantic equivalence automatically.

## Reading Prioritization Results

A `prioritization_result` is a ranked follow-up list.

Each target includes:

- `target_id`
- `priority_rank`
- `message`
- `rule_trace`

`rule_trace` explains why the target was ranked.

Prioritization is not a final quality judgment. It is an interpretable queue for follow-up analysis.

## Lightweight Interpretation Layer

The tool includes a preliminary simplified interpretation operation:

- `summarize`

It produces a compact `summary_result` from one or more existing result documents.

This component does not replace the raw outputs. It sits on top of them.

It is deterministic and rule-based.

The summary does not use AI interpretation. It selects signals using fixed rules:

- coverage findings are ordered by fixed coverage severity
- comparison signals use the already ranked comparison observations
- alignment gaps use the already ranked alignment observations
- prioritization signals use the already ranked target list
- only a small fixed number of strongest signals is promoted

The CLI can also render the same deterministic summary as Markdown:

```bash
dpawb summarize --result comparison.json --format markdown
```

Example output shape:

```json
{
  "result_type": "summary_result",
  "inputs": {
    "result_count": 2
  },
  "content": {
    "headline": "Both compared profiles satisfy the selected use case; main differences are constraint explicitness and modelling compactness.",
    "key_points": [
      "Coverage is representable on both sides.",
      "BatteryPass is more compact on the reduced slice.",
      "CE-RISE represents the same concepts through a composed model set."
    ],
    "follow_up_questions": [
      "Should compactness or modular extensibility matter more for this use case?"
    ]
  },
  "diagnostics": []
}
```

This would help humans and AI agents interpret rich outputs consistently while preserving deterministic analysis underneath.
