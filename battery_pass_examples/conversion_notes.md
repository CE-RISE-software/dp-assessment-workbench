# BatteryPass Reduced Slice Conversion Notes

## Comparison target

The first reduced real comparison slice is:

- use case: `battery_product_identification`
- BatteryPass source category: `General Product Information v1.2.0`

## Authoritative source

Use the BatteryPass RDF/Turtle source model as the authoritative input:

- `https://raw.githubusercontent.com/batterypass/BatteryPassDataModel/main/BatteryPass/io.BatteryPass.GeneralProductInformation/1.2.0/GeneralProductInformation.ttl`

Do not derive the reduced slice from JSON or presentation-oriented documentation
unless the RDF source is missing needed semantics.

## Local SHACL proxy rule

The workbench currently compares SHACL inputs, so the BatteryPass side should be
represented locally as a near-faithful SHACL proxy.

That proxy should:

- preserve BatteryPass identifiers and concept names where possible
- preserve structural grouping where possible
- avoid normalization unless required by SHACL expression
- document any approximation explicitly

## Expected first-pass mapped content

For the reduced `battery_product_identification` use case, the proxy should aim
to represent at least:

- battery passport identifier
- product identifier
- manufacturer information
- battery category

Optional for the first pass:

- operator information
- battery status
- manufacturing place

## File plan

Planned local artifacts:

- `battery_pass_examples/models/general_product_information_1_2_0.shacl.ttl`
- `battery_pass_examples/profiles/battery_product_identification_batterypass.yaml`

## Current status

The first reduced SHACL proxy is now present at:

- `battery_pass_examples/models/general_product_information_1_2_0.shacl.ttl`

The current proxy expresses only the reduced comparison slice:

- `batteryPassportIdentifier`
- `productIdentifier`
- `batteryCategory`
- `manufacturerInformation`
- nested `contactName`
- nested `identifier`

## Explicit approximations

The current proxy is intentionally reduced and approximate in these ways:

- it uses a repository-local BatteryPass namespace rather than the original
  SAMM namespace structure
- it expresses the reduced slice as SHACL node and property shapes rather than
  preserving SAMM modeling idioms
- it does not yet include optional reduced-slice-adjacent properties such as
  `operatorInformation`, `batteryStatus`, or `manufacturingPlace`
- it does not yet express BatteryPass enumeration constraints such as the full
  `batteryCategory` value set
