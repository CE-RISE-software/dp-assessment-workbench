# Live Sources

Release 1 supports composition-profile sources that are either local Turtle files or live URLs.

## Examples

The repository includes example profiles for live CE-RISE SHACL sources:

- `ce_rise_examples/profiles/battery_dpp_representation_live.yaml`
- `ce_rise_examples/profiles/battery_product_identification_live.yaml`
- `ce_rise_examples/profiles/dp_record_metadata_live.yaml`
- `ce_rise_examples/profiles/traceability_and_life_cycle_events_live.yaml`
- `ce_rise_examples/profiles/metadata_focused_composition_live.yaml`
- `ce_rise_examples/profiles/metadata_and_traceability_live.yaml`
- `ce_rise_examples/profiles/metadata_slice_left_live.yaml`
- `ce_rise_examples/profiles/metadata_slice_right_live.yaml`

If you want a single live source, the metadata-oriented example is the main starting point:

```bash
./scripts/run-local.sh assess --profile ce_rise_examples/profiles/dp_record_metadata_live.yaml
```

If you want a composed profile, use:

```bash
./scripts/run-local.sh assess --profile ce_rise_examples/profiles/metadata_and_traceability_live.yaml
```

You can also run the traceability-only example:

```bash
./scripts/run-local.sh assess --profile ce_rise_examples/profiles/traceability_and_life_cycle_events_live.yaml
```

Or through an installed CLI:

```bash
dpawb assess --profile ce_rise_examples/profiles/dp_record_metadata_live.yaml
```

## Coverage examples

The repository also includes CE-RISE-oriented use-case examples:

- `ce_rise_examples/use_cases/battery_dpp_representation.yaml`
- `ce_rise_examples/use_cases/battery_product_identification.yaml`
- `ce_rise_examples/use_cases/record_identity_lookup.yaml`
- `ce_rise_examples/use_cases/provenance_actor_lookup.yaml`

Example:

```bash
./scripts/run-local.sh coverage \
  --profile ce_rise_examples/profiles/dp_record_metadata_live.yaml \
  --use-case ce_rise_examples/use_cases/record_identity_lookup.yaml
```

For the real CE-RISE versus BatteryPass comparison effort, the main starting use case is:

- `ce_rise_examples/use_cases/battery_dpp_representation.yaml`

This keeps the first shared scope intentionally narrow:

- passport identity
- battery identity
- version or revision
- one responsible actor
- one battery type or classification signal

The matching CE-RISE starting composition for that use case is:

- `ce_rise_examples/profiles/battery_dpp_representation_live.yaml`

This currently composes:

- `dp_record_metadata`
- `traceability_and_life_cycle_events`

Under the current release-1 matcher, this CE-RISE composition is a reasonable starting profile, but it still yields several `indeterminate` findings for the battery-DPP use case. That is useful: it gives a real target for improving coverage matching before or while building the BatteryPass-side proxy.

For the first reduced real comparison pass, use:

- `ce_rise_examples/use_cases/battery_product_identification.yaml`
- `ce_rise_examples/profiles/battery_product_identification_live.yaml`

This narrower CE-RISE slice composes:

- `dp_record_metadata`
- `product_profile`

and is the intended first comparison baseline against BatteryPass General Product Information.

## Comparison examples

For manual pairwise comparison, use the comparison-ready live pair:

- `ce_rise_examples/profiles/metadata_slice_left_live.yaml`
- `ce_rise_examples/profiles/metadata_slice_right_live.yaml`
- `ce_rise_examples/alignments/metadata_slice_alignment.yaml` as a starting-point alignment example

Example:

```bash
./scripts/run-local.sh assess --profile ce_rise_examples/profiles/metadata_slice_left_live.yaml --output /tmp/left.json
./scripts/run-local.sh assess --profile ce_rise_examples/profiles/metadata_slice_right_live.yaml --output /tmp/right.json
./scripts/run-local.sh compare --left /tmp/left.json --right /tmp/right.json
```

Alignment-aware example:

```bash
./scripts/run-local.sh compare \
  --left /tmp/left.json \
  --right /tmp/right.json \
  --alignment ce_rise_examples/alignments/metadata_slice_alignment.yaml
```

For alignment-aware comparison results, inspect:

- `alignment_coverage_ratio` for the overall declared-match coverage
- `evaluated_pairs` for the full per-pair presence status
- `ranked_alignment_observations` for declared matches that are `left_only`, `right_only`, or `missing_both`

Those ranked alignment observations are the main review queue for analyst follow-up when a declared equivalence is not matched on both sides.

## Notes

- `fixtures/` is reserved for synthetic local validation assets only.
- `ce_rise_examples/` is reserved for real CE-RISE example inputs.
- Live URL fetching is allowed in the contract.
- Release 1 does not cache fetched sources across runs.
- If reproducibility matters, use a pinned URL or a locally captured Turtle file instead.
- CI validation intentionally does not depend on live network sources; it uses synthetic local fixtures only.
