# Digital Passport Model Assessment Workbench

A Python toolkit and thin CLI for SHACL-based assessment of digital passport data models, pairwise comparison of composed solutions, and SHACL-only use-case coverage analysis.

This README is primarily a repository and development entry point. The user-facing conceptual and usage reference is in [docs](docs/index.md).

---

## What this repository contains

- A publishable Python package with a CLI entry point: `dpawb`
- Contract-aligned input schemas for composition profiles, use cases, and alignments
- Built-in vocabularies and templates exposed through discovery commands
- Synthetic local fixtures used only for tests and validation
- A progression-based examples tree for human and AI-agent tutorials

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
- `summarize`

## AI-agent use

The intended primary integration mode is an AI agent orchestrating the analytical pipeline through the package API or the CLI. In practice, this means:

- deterministic file-based inputs
- JSON outputs suitable for agent parsing and chaining
- explicit analytical steps instead of a chat-oriented interface

The CLI remains useful for direct human invocation, but the main product shape is an analytical engine that can be called by agent skills, workflow runners, or future tool adapters.

An MCP server is a sensible next integration step. The current command surface already maps cleanly to MCP-style tools such as:

- `assess`
- `coverage`
- `compare`
- `prioritize`
- `schema`
- `vocabulary`
- `template`
- `capabilities`
- `summarize`

So yes: this repository can reasonably grow toward a dedicated MCP server, containerized for Docker distribution and later publication in an MCP server registry. The clean approach is:

- keep `dpawb` as the core Python package
- add a thin MCP server wrapper on top of the existing package API
- ship that wrapper as a separate runtime entry point and Docker image
- publish the MCP-facing metadata only after the tool contract is stable enough

The current contract-level alignment for that future step is documented in [docs/mcp-readiness.md](docs/mcp-readiness.md).

The public Python API is documented in [docs/api-reference.md](docs/api-reference.md).

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
dpawb summarize --result comparison_result.json --format markdown
dpawb capabilities
```

## Local Release Check

Before wiring PyPI CI/CD, run the local packaging check in an environment with `wheel` available:

```bash
make release-check
```

This builds a wheel and sdist, installs the wheel into a clean temporary environment, and runs installed CLI smoke checks.

## Structure

There are two distinct input areas in this repository:

- `fixtures/`
  Synthetic, repository-local test data only.
  These files are used by tests, smoke checks, and CI validation.

- `examples/01-source-ingestion/`
  Live-source example inputs intended for manual runs.
  These are the first step in the tutorial progression and are not part of CI validation.

The full examples tree is organized by analytical task, not by input data model:

- `examples/01-source-ingestion/`
  Load and assess declared profiles.
- `examples/02-structural-comparison/`
  Compare two profile assessment results.
- `examples/03-reduced-use-case-comparison/`
  Run the first aligned use-case comparison.
- `examples/04-extended-use-case-comparison/`
  Run a broader aligned use-case comparison.

Each example is usable by humans as a step-by-step command tutorial and by AI agents as a deterministic recipe over explicit files.

## Source-ingestion examples

Example profiles for live SHACL sources are included at:

- `examples/01-source-ingestion/profiles/battery_dpp_representation_live.yaml`
- `examples/01-source-ingestion/profiles/battery_product_identification_live.yaml`
- `examples/01-source-ingestion/profiles/dp_record_metadata_live.yaml`
- `examples/01-source-ingestion/profiles/traceability_and_life_cycle_events_live.yaml`
- `examples/01-source-ingestion/profiles/metadata_focused_composition_live.yaml`
- `examples/01-source-ingestion/profiles/metadata_and_traceability_live.yaml`
- `examples/02-structural-comparison/profiles/metadata_slice_left_live.yaml`
- `examples/02-structural-comparison/profiles/metadata_slice_right_live.yaml`

If you want a single live source, the metadata-oriented example is the main starting point:

```bash
./scripts/run-local.sh assess --profile examples/01-source-ingestion/profiles/dp_record_metadata_live.yaml
```

If you want a composed profile, use:

```bash
./scripts/run-local.sh assess --profile examples/01-source-ingestion/profiles/metadata_and_traceability_live.yaml
```

You can also run the traceability-only example:

```bash
./scripts/run-local.sh assess --profile examples/01-source-ingestion/profiles/traceability_and_life_cycle_events_live.yaml
```

For manual coverage runs, example use cases are included at:

- `examples/01-source-ingestion/use_cases/battery_dpp_representation.yaml`
- `examples/01-source-ingestion/use_cases/battery_product_identification.yaml`
- `examples/01-source-ingestion/use_cases/battery_passport_metadata_and_classification.yaml`
- `examples/01-source-ingestion/use_cases/record_identity_lookup.yaml`
- `examples/01-source-ingestion/use_cases/provenance_actor_lookup.yaml`

Example:

```bash
./scripts/run-local.sh coverage \
  --profile examples/01-source-ingestion/profiles/dp_record_metadata_live.yaml \
  --use-case examples/01-source-ingestion/use_cases/record_identity_lookup.yaml
```

The main real comparison-driver use case is:

- `examples/01-source-ingestion/use_cases/battery_dpp_representation.yaml`

It intentionally stays narrow. It requires:

- passport identity
- battery identity
- passport version or revision
- one responsible actor
- one battery type or classification signal

and the joins needed to treat those as one battery-DPP representation slice.

The matching starting composition for that use case is:

- `examples/01-source-ingestion/profiles/battery_dpp_representation_live.yaml`

It currently composes:

- `dp_record_metadata`
- `traceability_and_life_cycle_events`

This is the current broader baseline for the battery-DPP comparison work.

For the first reduced real pass, the narrower identity-focused comparison slice is:

- canonical example folder:
  `examples/03-reduced-use-case-comparison/`
- use case:
  `examples/03-reduced-use-case-comparison/use_cases/use_case.yaml`
- left profile:
  `examples/03-reduced-use-case-comparison/profiles/left_profile.yaml`
- right profile:
  `examples/03-reduced-use-case-comparison/profiles/right_profile.yaml`

This reduced slice composes:

- `dp_record_metadata`
- `product_profile`
- `traceability_and_life_cycle_events`

and is the first validated product-identification comparison slice against the
BatteryPass General Product Information model.

A second broader validated slice is also included:

- canonical example folder:
  `examples/04-extended-use-case-comparison/`
- use case:
  `examples/04-extended-use-case-comparison/use_cases/use_case.yaml`
- left profile:
  `examples/04-extended-use-case-comparison/profiles/left_profile.yaml`
- right profile:
  `examples/04-extended-use-case-comparison/profiles/right_profile.yaml`

This slice adds passport version/revision and battery type/classification while keeping the same CE-RISE composed model set.

The two current cross-ecosystem validation notes are:

- `examples/03-reduced-use-case-comparison/notes/comparison_note.md`
- `examples/04-extended-use-case-comparison/notes/comparison_note.md`

The step-by-step user reference for these examples is in [docs/example-applications.md](docs/example-applications.md).

For manual comparison runs, a comparison-ready live pair is included with the same declared scope label:

- `examples/02-structural-comparison/profiles/metadata_slice_left_live.yaml`
- `examples/02-structural-comparison/profiles/metadata_slice_right_live.yaml`
- `examples/02-structural-comparison/alignments/metadata_slice_alignment.yaml` as a starting-point alignment example

Typical flow:

```bash
./scripts/run-local.sh assess --profile examples/02-structural-comparison/profiles/metadata_slice_left_live.yaml --output /tmp/left.json
./scripts/run-local.sh assess --profile examples/02-structural-comparison/profiles/metadata_slice_right_live.yaml --output /tmp/right.json
./scripts/run-local.sh compare --left /tmp/left.json --right /tmp/right.json
```

With an explicit analyst-authored alignment:

```bash
./scripts/run-local.sh compare \
  --left /tmp/left.json \
  --right /tmp/right.json \
  --alignment examples/02-structural-comparison/alignments/metadata_slice_alignment.yaml
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
- join coverage can be satisfied by a shared owner shape, an explicit cross-shape object-reference path, or record-level retrieval context when that is the intended analytical interpretation

## Repository layout

- `src/dpawb/`: package, CLI, and analytical operations
- `src/dpawb/data/`: bundled schemas, vocabularies, and templates
- `fixtures/`: synthetic repository-local models, profiles, use cases, and alignments for tests only
- `examples/01-source-ingestion/`: source-ingestion profiles, use cases, and alignments for manual runs
- `examples/03-reduced-use-case-comparison/`: self-contained aligned use-case comparison examples
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
