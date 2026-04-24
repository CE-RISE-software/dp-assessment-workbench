# Source Ingestion Examples

Release 1 supports composition-profile sources that are either local Turtle files or live URLs.

This page is the first tutorial step in the examples progression. It shows how a human or an AI agent can start from declared profile files and run deterministic assessment or coverage commands.

## Examples

The source-ingestion examples use live SHACL URLs as inputs:

- `examples/01-source-ingestion/profiles/battery_dpp_representation_live.yaml`
- `examples/01-source-ingestion/profiles/battery_product_identification_live.yaml`
- `examples/01-source-ingestion/profiles/dp_record_metadata_live.yaml`
- `examples/01-source-ingestion/profiles/traceability_and_life_cycle_events_live.yaml`
- `examples/01-source-ingestion/profiles/metadata_focused_composition_live.yaml`
- `examples/01-source-ingestion/profiles/metadata_and_traceability_live.yaml`
- `examples/02-structural-comparison/profiles/metadata_slice_left_live.yaml`
- `examples/02-structural-comparison/profiles/metadata_slice_right_live.yaml`

If you want a single live source, the metadata-oriented example is the main starting point:

```bash
./scripts/run-local.sh assess --profile examples/01-source-ingestion/profiles/dp_record_metadata_live.yaml
```

If you want a composed profile, use:

```bash
./scripts/run-local.sh assess --profile examples/01-source-ingestion/profiles/metadata_and_traceability_live.yaml
```

You can also run the traceability-only example:

```bash
./scripts/run-local.sh assess --profile examples/01-source-ingestion/profiles/traceability_and_life_cycle_events_live.yaml
```

Or through an installed CLI:

```bash
dpawb assess --profile examples/01-source-ingestion/profiles/dp_record_metadata_live.yaml
```

## Coverage Examples

The repository also includes use-case examples for coverage runs:

- `examples/01-source-ingestion/use_cases/battery_dpp_representation.yaml`
- `examples/01-source-ingestion/use_cases/battery_product_identification.yaml`
- `examples/01-source-ingestion/use_cases/battery_passport_metadata_and_classification.yaml`
- `examples/01-source-ingestion/use_cases/record_identity_lookup.yaml`
- `examples/01-source-ingestion/use_cases/provenance_actor_lookup.yaml`

Example:

```bash
./scripts/run-local.sh coverage \
  --profile examples/01-source-ingestion/profiles/dp_record_metadata_live.yaml \
  --use-case examples/01-source-ingestion/use_cases/record_identity_lookup.yaml
```

For the broader battery-DPP comparison effort, the main starting use case is:

- `examples/01-source-ingestion/use_cases/battery_dpp_representation.yaml`

This keeps the first shared scope intentionally narrow:

- passport identity
- battery identity
- version or revision
- one responsible actor
- one battery type or classification signal

The matching starting composition for that use case is:

- `examples/01-source-ingestion/profiles/battery_dpp_representation_live.yaml`

This currently composes:

- `dp_record_metadata`
- `traceability_and_life_cycle_events`

This remains a broader exploratory baseline for the battery-DPP scope, but it is not the main validated comparison slice.

For the first reduced real comparison pass, use:

- `examples/03-reduced-use-case-comparison/`

This narrower left-side slice composes:

- `dp_record_metadata`
- `product_profile`
- `traceability_and_life_cycle_events`

and is the first validated comparison baseline against the right-side General Product Information proxy.

A second broader validated comparison slice is also included:

- `examples/04-extended-use-case-comparison/`

This adds:

- passport version or revision
- battery type or classification

while staying inside the same composed left-side model set.

## Comparison examples

For manual pairwise comparison, use the comparison-ready live pair:

- `examples/02-structural-comparison/profiles/metadata_slice_left_live.yaml`
- `examples/02-structural-comparison/profiles/metadata_slice_right_live.yaml`
- `examples/02-structural-comparison/alignments/metadata_slice_alignment.yaml` as a starting-point alignment example

Example:

```bash
./scripts/run-local.sh assess --profile examples/02-structural-comparison/profiles/metadata_slice_left_live.yaml --output /tmp/left.json
./scripts/run-local.sh assess --profile examples/02-structural-comparison/profiles/metadata_slice_right_live.yaml --output /tmp/right.json
./scripts/run-local.sh compare --left /tmp/left.json --right /tmp/right.json
```

Alignment-aware example:

```bash
./scripts/run-local.sh compare \
  --left /tmp/left.json \
  --right /tmp/right.json \
  --alignment examples/02-structural-comparison/alignments/metadata_slice_alignment.yaml
```

For alignment-aware comparison results, inspect:

- `alignment_coverage_ratio` for the overall declared-match coverage
- `evaluated_pairs` for the full per-pair presence status
- `ranked_alignment_observations` for declared matches that are `left_only`, `right_only`, or `missing_both`

Those ranked alignment observations are the main review queue for analyst follow-up when a declared equivalence is not matched on both sides.

## Notes

- `fixtures/` is reserved for synthetic local validation assets only.
- `examples/01-source-ingestion/` demonstrates live URL source loading.
- `examples/03-reduced-use-case-comparison/` and `examples/04-extended-use-case-comparison/` demonstrate aligned use-case comparison.
- Live URL fetching is allowed in the contract.
- Release 1 does not cache fetched sources across runs.
- If reproducibility matters, use a pinned URL or a locally captured Turtle file instead.
- CI validation intentionally does not depend on live network sources; it uses synthetic local fixtures only.
