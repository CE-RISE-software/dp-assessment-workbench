# Composition Recommendation

This example recommends a combined profile from two already assessed model sets.

It uses the same reduced CE-RISE and BatteryPass inputs as the product-identification comparison example, but asks a different question:

- comparison asks how the two model sets differ
- recommendation asks which pieces should be combined and which declared equivalent entities need deduplication review

The recommendation is a decision-support result. It proposes a combined composition profile and explains the inclusion and deduplication signals used to build that proposal. It does not create a new SHACL model.

## Files

- left profile: [profiles/left_profile.yaml](profiles/left_profile.yaml)
- right profile: [profiles/right_profile.yaml](profiles/right_profile.yaml)
- use case: [use_cases/use_case.yaml](use_cases/use_case.yaml)
- alignment: [alignments/alignment.yaml](alignments/alignment.yaml)
- right-side SHACL proxy: [models/general_product_information_1_2_0.shacl.ttl](models/general_product_information_1_2_0.shacl.ttl)
- intermediate assessment, coverage, and comparison results: [results/](results/)
- example recommendation result: [results/recommendation.json](results/recommendation.json)

## Step-by-step Run

```bash
./scripts/run-local.sh assess \
  --profile examples/05-composition-recommendation/profiles/left_profile.yaml \
  --output /tmp/recommend_left_assessment.json

./scripts/run-local.sh assess \
  --profile examples/05-composition-recommendation/profiles/right_profile.yaml \
  --output /tmp/recommend_right_assessment.json

./scripts/run-local.sh coverage \
  --profile examples/05-composition-recommendation/profiles/left_profile.yaml \
  --use-case examples/05-composition-recommendation/use_cases/use_case.yaml \
  --output /tmp/recommend_left_coverage.json

./scripts/run-local.sh coverage \
  --profile examples/05-composition-recommendation/profiles/right_profile.yaml \
  --use-case examples/05-composition-recommendation/use_cases/use_case.yaml \
  --output /tmp/recommend_right_coverage.json

./scripts/run-local.sh compare \
  --left /tmp/recommend_left_assessment.json \
  --right /tmp/recommend_right_assessment.json \
  --alignment examples/05-composition-recommendation/alignments/alignment.yaml \
  --output /tmp/recommend_comparison.json

./scripts/run-local.sh recommend-composition \
  --left /tmp/recommend_left_assessment.json \
  --right /tmp/recommend_right_assessment.json \
  --comparison /tmp/recommend_comparison.json \
  --coverage /tmp/recommend_left_coverage.json /tmp/recommend_right_coverage.json \
  --output /tmp/recommendation.json
```

## Result Shape

The recommendation result contains:

- a proposed `candidate_profile`
  The profile that could be assessed or implemented next.
- module-level inclusion recommendations
  The modules from each side that the workbench suggests keeping.
- alignment-based entity deduplication recommendations
  Declared equivalent properties or concepts that look duplicated across the two sides.
- review items that must be inspected before implementing an actual combined SHACL model

The command is deterministic. It does not rewrite SHACL; it emits a proposed profile and traceable review decisions.
