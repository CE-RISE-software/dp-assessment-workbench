# Primary Example: Battery Product Identification

This is the primary worked aligned use-case comparison example.

It compares a reduced `battery_product_identification` scope.

This folder is a tutorial for both humans and AI agents. The commands below are intentionally explicit so the same sequence can be run manually or orchestrated from an agent skill.

## Purpose

This example checks whether both input profiles can represent the minimum product-identification slice:

- passport identifier
- battery/product identifier
- battery category
- manufacturer information
- battery-to-category retrieval
- battery-to-manufacturer responsibility link

## Files

- left profile: [profiles/left_profile.yaml](profiles/left_profile.yaml)
- right profile: [profiles/right_profile.yaml](profiles/right_profile.yaml)
- use case: [use_cases/use_case.yaml](use_cases/use_case.yaml)
- alignment: [alignments/alignment.yaml](alignments/alignment.yaml)
- right-side SHACL proxy: [models/general_product_information_1_2_0.shacl.ttl](models/general_product_information_1_2_0.shacl.ttl)
- comparison note: [notes/comparison_note.md](notes/comparison_note.md)
- deterministic summary JSON: [results/summary.json](results/summary.json)
- deterministic summary Markdown: [results/summary.md](results/summary.md)

## Step-by-step Run

```bash
./scripts/run-local.sh coverage \
  --profile examples/03-reduced-use-case-comparison/profiles/left_profile.yaml \
  --use-case examples/03-reduced-use-case-comparison/use_cases/use_case.yaml \
  --output /tmp/primary_left_coverage.json

./scripts/run-local.sh coverage \
  --profile examples/03-reduced-use-case-comparison/profiles/right_profile.yaml \
  --use-case examples/03-reduced-use-case-comparison/use_cases/use_case.yaml \
  --output /tmp/primary_right_coverage.json

./scripts/run-local.sh assess \
  --profile examples/03-reduced-use-case-comparison/profiles/left_profile.yaml \
  --output /tmp/primary_left_assessment.json

./scripts/run-local.sh assess \
  --profile examples/03-reduced-use-case-comparison/profiles/right_profile.yaml \
  --output /tmp/primary_right_assessment.json

./scripts/run-local.sh compare \
  --left /tmp/primary_left_assessment.json \
  --right /tmp/primary_right_assessment.json \
  --alignment examples/03-reduced-use-case-comparison/alignments/alignment.yaml \
  --output /tmp/primary_comparison.json

./scripts/run-local.sh prioritize \
  --assessment /tmp/primary_left_assessment.json \
  --comparison /tmp/primary_comparison.json \
  --coverage /tmp/primary_left_coverage.json \
  --output /tmp/primary_prioritization.json

./scripts/run-local.sh summarize \
  --result /tmp/primary_left_coverage.json \
  --result /tmp/primary_right_coverage.json \
  --result /tmp/primary_comparison.json \
  --result /tmp/primary_prioritization.json \
  --format markdown
```

## Current Result

Both sides are currently classified as `representable` for this reduced use case.

The declared alignment currently matches all four declared equivalences.
