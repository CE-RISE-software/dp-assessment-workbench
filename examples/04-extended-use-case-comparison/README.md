# Extended Validation: Passport Metadata And Classification

This is an extended validation slice, not a second primary example.

It checks whether the primary example behavior generalizes when version/revision and type/classification semantics are added.

This folder reuses the same deterministic tutorial pattern as the reduced example, but with a broader use-case scope.

## Purpose

This example validates a broader `battery_passport_metadata_and_classification` scope:

- passport identifier
- battery/product identifier
- passport version or revision
- battery type or classification
- passport-to-version provenance context
- battery-to-classification retrieval context

## Files

- left profile: [profiles/left_profile.yaml](profiles/left_profile.yaml)
- right profile: [profiles/right_profile.yaml](profiles/right_profile.yaml)
- use case: [use_cases/use_case.yaml](use_cases/use_case.yaml)
- alignment: [alignments/alignment.yaml](alignments/alignment.yaml)
- right-side SHACL proxy: [models/general_product_information_with_version_1_2_0.shacl.ttl](models/general_product_information_with_version_1_2_0.shacl.ttl)
- comparison note: [notes/comparison_note.md](notes/comparison_note.md)
- deterministic summary JSON: [results/summary.json](results/summary.json)
- deterministic summary Markdown: [results/summary.md](results/summary.md)

## Step-by-step Run

```bash
./scripts/run-local.sh coverage \
  --profile examples/04-extended-use-case-comparison/profiles/left_profile.yaml \
  --use-case examples/04-extended-use-case-comparison/use_cases/use_case.yaml \
  --output /tmp/extended_left_coverage.json

./scripts/run-local.sh coverage \
  --profile examples/04-extended-use-case-comparison/profiles/right_profile.yaml \
  --use-case examples/04-extended-use-case-comparison/use_cases/use_case.yaml \
  --output /tmp/extended_right_coverage.json

./scripts/run-local.sh assess \
  --profile examples/04-extended-use-case-comparison/profiles/left_profile.yaml \
  --output /tmp/extended_left_assessment.json

./scripts/run-local.sh assess \
  --profile examples/04-extended-use-case-comparison/profiles/right_profile.yaml \
  --output /tmp/extended_right_assessment.json

./scripts/run-local.sh compare \
  --left /tmp/extended_left_assessment.json \
  --right /tmp/extended_right_assessment.json \
  --alignment examples/04-extended-use-case-comparison/alignments/alignment.yaml \
  --output /tmp/extended_comparison.json

./scripts/run-local.sh prioritize \
  --assessment /tmp/extended_left_assessment.json \
  --comparison /tmp/extended_comparison.json \
  --coverage /tmp/extended_left_coverage.json \
  --output /tmp/extended_prioritization.json

./scripts/run-local.sh summarize \
  --result /tmp/extended_left_coverage.json \
  --result /tmp/extended_right_coverage.json \
  --result /tmp/extended_comparison.json \
  --result /tmp/extended_prioritization.json \
  --format markdown
```

## Current Result

Both sides are currently classified as `representable` for this broader validation slice.

The declared alignment currently matches all four declared equivalences.
