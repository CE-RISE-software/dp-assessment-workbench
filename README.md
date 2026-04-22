# Digital Passport Model Assessment Workbench

A Python toolkit and thin CLI for SHACL-based assessment of digital passport data models, pairwise comparison of composed solutions, and SHACL-only use-case coverage analysis.

---

## What this repository contains

- A publishable Python package with a CLI entry point: `dpawb`
- Contract-aligned input schemas for composition profiles, use cases, and alignments
- Built-in vocabularies and templates exposed through discovery commands
- Synthetic local fixtures used only for tests and validation
- Separate example inputs for real CE-RISE live sources

## Release-1 shape

The release-1 tool is designed primarily as an agent-usable analytical toolkit with a thin CLI. The core command surface is:

- `assess`
- `coverage`
- `compare`
- `prioritize`
- `schema`
- `vocabulary`
- `template`
- `capabilities`

## Install

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e .
```

If you are working in a restricted environment, the package is configured to build with `setuptools` so editable installs do not depend on fetching an extra build backend.

If build isolation or wheel support is unavailable locally, use:

```bash
python -m pip install --no-build-isolation -e .
```

In constrained environments where editable installation is blocked by local Python packaging tooling, the repository still supports a repo-native execution path:

```bash
./scripts/run-local.sh capabilities
./scripts/test-local.sh
make smoke
make test
make validate
```

## Example commands

```bash
dpawb assess --profile fixtures/profiles/synthetic_evolution_latest.yaml
dpawb coverage --profile fixtures/profiles/synthetic_evolution_latest.yaml --use-case fixtures/use_cases/product_identity_lookup.yaml
dpawb compare --left left_assessment.json --right right_assessment.json
dpawb capabilities
```

## Structure

There are two distinct input areas in this repository:

- `fixtures/`
  Synthetic, repository-local test data only.
  These files are used by tests, smoke checks, and CI validation.

- `ce_rise_examples/`
  Real CE-RISE example inputs intended for manual runs.
  These are opt-in examples and are not part of CI validation.

## Live-source examples

Example profiles for live CE-RISE SHACL sources are included at:

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

For manual coverage runs, example CE-RISE-oriented use cases are included at:

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

The main real comparison-driver use case is:

- `ce_rise_examples/use_cases/battery_dpp_representation.yaml`

It intentionally stays narrow. It requires:

- passport identity
- battery identity
- passport version or revision
- one responsible actor
- one battery type or classification signal

and the joins needed to treat those as one battery-DPP representation slice.

The matching CE-RISE starting composition for that use case is:

- `ce_rise_examples/profiles/battery_dpp_representation_live.yaml`

It currently composes:

- `dp_record_metadata`
- `traceability_and_life_cycle_events`

This is the current CE-RISE baseline for the real CE-RISE versus BatteryPass comparison work.

For the first reduced real pass, the narrower identity-focused comparison slice is:

- use case:
  `ce_rise_examples/use_cases/battery_product_identification.yaml`
- CE-RISE profile:
  `ce_rise_examples/profiles/battery_product_identification_live.yaml`

This reduced slice composes:

- `dp_record_metadata`
- `product_profile`

and is intended as the first product-identification comparison against the
BatteryPass General Product Information model.

For manual comparison runs, a comparison-ready live pair is included with the same declared scope label:

- `ce_rise_examples/profiles/metadata_slice_left_live.yaml`
- `ce_rise_examples/profiles/metadata_slice_right_live.yaml`
- `ce_rise_examples/alignments/metadata_slice_alignment.yaml` as a starting-point alignment example

Typical flow:

```bash
./scripts/run-local.sh assess --profile ce_rise_examples/profiles/metadata_slice_left_live.yaml --output /tmp/left.json
./scripts/run-local.sh assess --profile ce_rise_examples/profiles/metadata_slice_right_live.yaml --output /tmp/right.json
./scripts/run-local.sh compare --left /tmp/left.json --right /tmp/right.json
```

With an explicit analyst-authored alignment:

```bash
./scripts/run-local.sh compare \
  --left /tmp/left.json \
  --right /tmp/right.json \
  --alignment ce_rise_examples/alignments/metadata_slice_alignment.yaml
```

When an alignment file is provided, the comparison result now includes two alignment-oriented views:

- `evaluated_pairs`
  Full per-pair presence status for every declared equivalence.

- `ranked_alignment_observations`
  Review-oriented gaps for any declared pair that is only present on one side or missing on both sides.

So the main things to inspect in an alignment-aware comparison result are:

- `alignment_coverage_ratio`
- `evaluated_pairs`
- `ranked_alignment_observations`

If that comparison result is then passed into `prioritize`, those alignment gaps can also appear directly as ranked improvement targets.

The current analytical core is still conservative by design, but it now goes beyond token matching alone:

- contradiction detection covers direct cardinality conflicts and datatype-versus-object-reference conflicts
- item coverage uses SHACL path, owner-shape, and target-class evidence
- join coverage can be satisfied by either a shared owner shape or an explicit cross-shape object-reference path

## Repository layout

- `src/dpawb/`: package, CLI, and analytical operations
- `src/dpawb/data/`: bundled schemas, vocabularies, and templates
- `fixtures/`: synthetic repository-local models, profiles, use cases, and alignments for tests only
- `ce_rise_examples/`: opt-in real CE-RISE example profiles, use cases, and alignments for manual runs
- `battery_pass_examples/`: real comparison notes and source-selection artifacts for the BatteryPass side
- `scripts/`: repo-native execution and test helpers
- `.github/workflows/validate.yml` and `.forgejo/workflows/validate.yml`: CI validation via the repo-native path
- `AGENTS.md`: project contract and release-1 decisions


## License

Licensed under the [European Union Public Licence v1.2 (EUPL-1.2)](LICENSE).

## Contributing

This repository is maintained on [Codeberg](https://codeberg.org/CE-RISE-software/dp-assessment-workbench) — the canonical source of truth. The GitHub repository is a read mirror used for release archival and Zenodo integration. Issues and pull requests should be opened on Codeberg.

---

<a href="https://europa.eu" target="_blank" rel="noopener noreferrer">
  <img src="https://ce-rise.eu/wp-content/uploads/2023/01/EN-Funded-by-the-EU-PANTONE-e1663585234561-1-1.png" alt="EU emblem" width="200"/>
</a>

Funded by the European Union under Grant Agreement No. 101092281 — CE-RISE.  
Views and opinions expressed are those of the author(s) only and do not necessarily reflect those of the European Union or the granting authority (HADEA).
Neither the European Union nor the granting authority can be held responsible for them.

© 2026 CE-RISE consortium.  
Licensed under the [European Union Public Licence v1.2 (EUPL-1.2)](LICENSE).  
Attribution: CE-RISE project (Grant Agreement No. 101092281) and the individual authors/partners as indicated.

<a href="https://www.nilu.com" target="_blank" rel="noopener noreferrer">
  <img src="https://nilu.no/wp-content/uploads/2023/12/nilu-logo-seagreen-rgb-300px.png" alt="NILU logo" height="20"/>
</a>

Developed by NILU (Riccardo Boero — ribo@nilu.no) within the CE-RISE project.
