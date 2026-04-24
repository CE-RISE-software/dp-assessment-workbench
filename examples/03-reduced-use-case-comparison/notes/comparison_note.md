# First Reduced Comparison Note

This note records the first reduced comparison setup for `battery_product_identification`.

## Compared Inputs

- BatteryPass side:
  - source slice: `General Product Information v1.2.0`
  - local SHACL proxy: [general_product_information_1_2_0.shacl.ttl](../models/general_product_information_1_2_0.shacl.ttl)
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
- `battery_identifier`: `representable`
- `passport_identifier`: `representable`
- `battery_category`: `representable`
- `manufacturer_information`: `representable`
- `battery_to_category`: `representable`
- `battery_to_manufacturer`: `representable`

CE-RISE selected model set:

- overall: `representable`
- `battery_identifier`: `representable`
- `passport_identifier`: `representable`
- `battery_category`: `representable`
- `manufacturer_information`: `representable`
- `battery_to_category`: `representable`
- `battery_to_manufacturer`: `representable`

## What BatteryPass Supports More Directly

- The reduced BatteryPass slice exposes `battery_identifier` and `passport_identifier` more directly in one product-information structure.
- The reduced BatteryPass slice also gives a clearer direct path from the identified battery/product to manufacturer information.
- In the current reduced proxy, BatteryPass still presents the narrow identification slice in a more compact single-structure form.

## What CE-RISE Already Covers

- CE-RISE does expose matching signals for all four required items in the selected 3-model set.
- The current workbench now classifies all four required items and both required joins as `representable` on the selected CE-RISE set.
- The declared alignment matches all four selected equivalences:
  - passport identifier property
  - product identifier property
  - battery category property
  - manufacturer identifier property
- `product_profile` appears to carry the main product/category/manufacturer-side signals.
- `dp_record_metadata` appears to carry the passport-side signal.
- `traceability_and_life_cycle_events` is included in the selected set because it supports cross-model mapping for this slice.

## Real Model Differences

- CE-RISE distinguishes product-side and passport-side concepts more clearly, while the reduced BatteryPass slice presents them in a tighter single structure.
- BatteryPass is still more direct on this reduced slice for identifier retrieval and packaging.
- CE-RISE appears more distributed across a composed record-and-product architecture.
- This comparison should not treat product identity and passport identity as the same concept, even when BatteryPass places them close together.

## Current Workbench Limitations

- Coverage recognition on the reduced CE-RISE case is now good enough for this example, but the current logic still needs broader validation on additional composed cases.
- Structural comparison now foregrounds normalized explicitness and vocabulary signals, but raw count differences are still present in the result document because the CE-RISE comparison set is much larger than the reduced BatteryPass slice.
- The current prioritization output is now free of the earlier false CE-RISE coverage gaps and the noisiest raw count deltas, but it is still driven mainly by explicitness and maintainability signals rather than a richer notion of architectural quality.

## Immediate Interpretation

- The reduced comparison is a valid example application of the workbench.
- Both compared sides now satisfy the reduced identification use case under the current workbench rules.
- BatteryPass remains more compact and direct on this slice, while CE-RISE remains more distributed across the composed set.
- The current result is therefore useful both as a comparison example and as a basis for broader comparison interpretation beyond explicitness-focused signals.
