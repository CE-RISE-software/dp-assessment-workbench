# BatteryPass Real Comparison Notes

This directory captures the BatteryPass-side starting point for the reduced real
`battery_product_identification` comparison work.

## Current conclusion

BatteryPass already publishes platform-independent RDF/Turtle data model
artifacts per parameter category. That means the right starting point is:

- use the published RDF/Turtle source categories directly
- avoid starting from JSON/OpenAPI/AAS derivations
- only introduce a SHACL proxy layer where the current workbench requires it

## First selected BatteryPass slice

The first BatteryPass source category to use is:

- General Product Information v1.2.0

Primary sources:

- Documentation:
  `https://batterypass.github.io/BatteryPassDataModel//BatteryPass/io.BatteryPass.GeneralProductInformation/1.2.0/gen/GeneralProductInformation.html`
- RDF/Turtle source:
  `https://raw.githubusercontent.com/batterypass/BatteryPassDataModel/main/BatteryPass/io.BatteryPass.GeneralProductInformation/1.2.0/GeneralProductInformation.ttl`

Why this is the right first slice:

- it is explicitly product-specific
- it already covers the identity layer of a battery passport
- it includes actor/manufacturer/operator information
- it includes battery category/classification signals

## Observed BatteryPass data points relevant to the current reduced real use case

From the published General Product Information documentation, the following
properties are clearly relevant to `battery_product_identification`:

- `batteryPassportIdentifier`
- `productIdentifier`
- `manufacturerInformation`
- `operatorInformation`
- `batteryCategory`
- `batteryStatus`
- `manufacturingPlace`

## Immediate implication for the comparison work

For the current reduced real use case, BatteryPass appears to be stronger than
the current CE-RISE baseline on product-specific identity/classification
signals.

So the next BatteryPass-side work is:

1. keep the reduced source selection around General Product Information
2. create a near-faithful SHACL proxy only for that reduced slice
3. compare it against the CE-RISE reduced product-identification composition

## Local artifacts

- profile stub:
  `battery_pass_examples/profiles/battery_product_identification_batterypass.yaml`
- planned local SHACL proxy:
  `battery_pass_examples/models/general_product_information_1_2_0.shacl.ttl`
- conversion notes:
  `battery_pass_examples/conversion_notes.md`

## Deferred point

The broader `battery_dpp_representation` use case, including explicit version or
revision semantics, is deferred until after the first reduced comparison pass is
working.
