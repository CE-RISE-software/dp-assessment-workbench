# First Reduced Comparison Note

This note records the first reduced comparison setup for `battery_product_identification`.

## Compared Inputs

- BatteryPass side:
  - source slice: `General Product Information v1.2.0`
  - local SHACL proxy: [general_product_information_1_2_0.shacl.ttl](./models/general_product_information_1_2_0.shacl.ttl)
  - profile: [battery_product_identification_batterypass.yaml](./profiles/battery_product_identification_batterypass.yaml)
- CE-RISE side:
  - `dp_record_metadata`
  - `product_profile`
  - `traceability_and_life_cycle_events`
  - profile: [battery_product_identification_with_traceability_live.yaml](../ce_rise_examples/profiles/battery_product_identification_with_traceability_live.yaml)
- shared use case:
  - [battery_product_identification.yaml](../ce_rise_examples/use_cases/battery_product_identification.yaml)
- declared alignment:
  - [battery_product_identification_ce_rise_alignment.yaml](./alignments/battery_product_identification_ce_rise_alignment.yaml)

## Coverage Snapshot

BatteryPass reduced proxy:

- overall: `partially_representable`
- `battery_identifier`: `representable`
- `passport_identifier`: `representable`
- `battery_category`: `partially_representable`
- `manufacturer_information`: `partially_representable`
- `battery_to_category`: `partially_representable`
- `battery_to_manufacturer`: `partially_representable`

CE-RISE selected model set:

- overall: `partially_representable`
- `battery_identifier`: `partially_representable`
- `passport_identifier`: `partially_representable`
- `battery_category`: `partially_representable`
- `manufacturer_information`: `partially_representable`
- `battery_to_category`: `partially_representable`
- `battery_to_manufacturer`: `partially_representable`

## What BatteryPass Supports More Directly

- The reduced BatteryPass slice exposes `battery_identifier` and `passport_identifier` more directly in one product-information structure.
- The reduced BatteryPass slice also gives a clearer direct path from the identified battery/product to manufacturer information.
- In the current reduced proxy, BatteryPass is easier for the workbench to classify as `representable` on identifier fields.

## What CE-RISE Already Covers

- CE-RISE does expose matching signals for all four required items in the selected 3-model set.
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
- BatteryPass is more direct on this reduced slice for identifier retrieval.
- CE-RISE appears more distributed across a composed record-and-product architecture.
- This comparison should not treat product identity and passport identity as the same concept, even when BatteryPass places them close together.

## Current Workbench Limitations

- The workbench still scores CE-RISE identifier and manufacturer/category matches as only `partially_representable` even though the aligned properties are present.
- The current coverage logic is still better at direct single-structure matches than at composed cross-model CE-RISE patterns.
- Structural comparison still contains large size-driven deltas because the CE-RISE comparison set is much larger than the reduced BatteryPass slice.
- The current prioritization output is useful mainly for highlighting CE-RISE partial-coverage hotspots, not yet for producing a final judgment on architectural quality.

## Immediate Interpretation

- The reduced comparison is now valid enough to continue.
- BatteryPass currently looks easier to satisfy on the narrow identification slice.
- CE-RISE appears to contain the needed concepts, but the support is currently less direct under the workbench's present matching rules.
- The next work should improve CE-RISE-side recognition without collapsing genuine model differences.
