# Second Validation Slice Note

This note records a broader cross-ecosystem validation slice for `battery_passport_metadata_and_classification`.

## Compared Inputs

- BatteryPass side:
  - local SHACL proxy: [general_product_information_with_version_1_2_0.shacl.ttl](../models/general_product_information_with_version_1_2_0.shacl.ttl)
  - profile: [right_profile.yaml](../profiles/right_profile.yaml)
- CE-RISE side:
  - `dp_record_metadata`
  - `product_profile`
  - `traceability_and_life_cycle_events`
  - profile: [left_profile.yaml](../profiles/left_profile.yaml)
- shared use case:
  - [use_case.yaml](../use_cases/use_case.yaml)
- declared alignment:
  - [alignment.yaml](../alignments/alignment.yaml)

## Coverage Snapshot

BatteryPass reduced proxy:

- overall: `representable`
- `passport_identifier`: `representable`
- `battery_identifier`: `representable`
- `passport_version_or_revision`: `representable`
- `battery_type_or_classification`: `representable`
- `passport_to_version`: `representable`
- `battery_to_classification`: `representable`

CE-RISE selected model set:

- overall: `representable`
- `passport_identifier`: `representable`
- `battery_identifier`: `representable`
- `passport_version_or_revision`: `representable`
- `battery_type_or_classification`: `representable`
- `passport_to_version`: `representable`
- `battery_to_classification`: `representable`

## What This Slice Validates

- The improved semantic matching now generalizes beyond the first identification-only slice.
- `version` and `revision` are recognized as equivalent enough for this release-1 coverage layer.
- `type`, `category`, and `classification` are recognized as equivalent enough for this release-1 coverage layer.
- CE-RISE record-envelope retrieval context is now recognized well enough for `passport_to_version`.

## Comparison Snapshot

- declared alignment coverage: `1.0`
- all 4 selected equivalence pairs are matched
- the leading structural comparison signals remain normalized explicitness differences, not raw size counts

Current top comparison signals on this slice are:

- lower `constraint_density` on the BatteryPass reduced side
- higher `cardinality_bounded_property_share` on the BatteryPass reduced side
- lower `shared_vocabulary_overlap_ratio` across the cross-ecosystem pair
- slightly higher `typed_property_share` on the BatteryPass reduced side

## Prioritization Snapshot

Current prioritized targets remain narrow:

- `cardinality_bounded_property_share`
- `typed_property_share`
- redundancy summary on the assessed CE-RISE side

## Immediate Interpretation

- The workbench improvements now hold across both aligned use-case comparison slices.
- The current remaining differences are no longer about basic coverage recognition on these slices.
- The next quality step should therefore focus on richer comparison interpretation, not more token-level rescue work.
