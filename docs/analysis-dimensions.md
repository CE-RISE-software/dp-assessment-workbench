# Analysis Dimensions

The workbench analyzes SHACL-based digital passport model specifications without requiring representative instance datasets.

## Structural Size And Complexity

Structural metrics describe the scale and shape of a model composition.

Examples include:

- number of node shapes
- number of property shapes
- number of target declarations
- number of closed shapes
- number of datatype-constrained properties
- number of object-reference properties

These metrics help distinguish a compact model slice from a broader composed ecosystem.

## Explicitness And Constraint Readiness

Explicitness metrics describe how much of the model is directly constrained in SHACL.

Examples include:

- typed-property share
- cardinality-bounded-property share
- open-property share
- constraint density

These metrics are useful when comparing whether one model expresses constraints more directly than another.

## Structural Interoperability

Interoperability metrics describe relationships between modules in a composed profile.

Examples include:

- cross-module reference count
- cross-module reference share
- shared-vocabulary overlap count
- shared-vocabulary overlap ratio

Release 1 treats each top-level `models` entry in a composition profile as one module boundary.

## Maintainability Signals

Maintainability findings are directly detectable issues or candidates from the SHACL graph.

Examples include:

- contradictions
- dangling references
- redundancy candidates

These findings are intentionally conservative. They are meant to be inspectable signals, not hidden semantic judgments.

## Use-Case Coverage

Coverage analysis checks whether a declared use case can be represented from the composed SHACL model.

Use cases are declared as:

- required information items
- required joins or concept links

Coverage classes are:

- `representable`
- `partially_representable`
- `not_representable`
- `indeterminate`

The result is SHACL-only. It does not require instance data.

## Model Comparison

Comparison runs on two assessment result documents with the same `comparison_scope_label`.

It reports:

- metric values for both sides
- deltas
- normalized ranked observations
- optional alignment-aware comparison when an analyst-authored alignment file is supplied

This supports both version comparison and cross-ecosystem comparison.

## Prioritization

Prioritization consumes previous result documents and ranks follow-up targets.

Signals can come from:

- coverage gaps
- maintainability findings
- directional comparison deltas
- alignment gaps

The prioritization layer is rule-based and explainable by design.

## Result Interpretation

The `summarize` operation provides a lightweight interpretation layer over existing result documents.

It does not add new analysis. It extracts a concise headline, key points, and follow-up questions from already computed results.
