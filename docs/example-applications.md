# Example Progression

The repository examples show an increasing degree of analytical comparison.

They are not organized by data model. Data models are inputs inside each example.

The examples are written as a tutorial path for both humans and AI agents:

- Humans can read each folder README and run the commands step by step.
- AI agents can follow the same folders as deterministic task recipes, using the declared YAML inputs and JSON outputs.
- The numbered folders intentionally move from simpler operations to richer comparison workflows.

- [Source ingestion](../examples/01-source-ingestion/README.md)
  Load and assess composition profiles from live URL sources.
- [Structural comparison](../examples/02-structural-comparison/README.md)
  Compare two assessment results for profiles with the same declared scope.
- [Reduced use-case comparison](../examples/03-reduced-use-case-comparison/README.md)
  Run the first hand-checkable aligned use-case comparison.
- [Extended use-case comparison](../examples/04-extended-use-case-comparison/README.md)
  Run a broader aligned use-case comparison to exercise more coverage signals.
- [Composition recommendation](../examples/05-composition-recommendation/README.md)
  Recommend a combined profile from two assessed model sets.

## Why Five Folders?

The folders reflect the analysis workflow, not source ecosystems.

Read them in numerical order.

## Shared Preparation Pattern

The comparison examples are self-contained and follow the same preparation pattern:

1. Define the comparison scope.
2. Define the left composition profile.
3. Define the right composition profile.
4. Define the use-case YAML.
5. Define the analyst-authored alignment YAML.
6. Run coverage for the left profile.
7. Run coverage for the right profile.
8. Run assessment for the left profile.
9. Run assessment for the right profile.
10. Run comparison.
11. Run prioritization.
12. Run deterministic summarization.
13. Run composition recommendation when a combined profile is useful.

## Folder Layout

Each canonical example folder uses this structure:

```text
profiles/
use_cases/
alignments/
models/
notes/
results/
```

The `results/` folder contains deterministic summary outputs generated from the raw result documents.

The raw result documents can be regenerated from the step-by-step commands in each example README.

For agents, the important rule is that every step consumes explicit files and produces deterministic JSON or Markdown outputs. No hidden interpretation step is required to reproduce the example.

## Source Ingestion

Folder:

```text
examples/01-source-ingestion/
```

Purpose:

- exercise live URL loading
- assess composition profiles without local model files
- keep source selection separate from comparison logic

## Structural Comparison

Folder:

```text
examples/02-structural-comparison/
```

Purpose:

- assess two profiles
- compare their structural metrics
- optionally add an analyst-authored alignment file

## Reduced Use-Case Comparison

Folder:

```text
examples/03-reduced-use-case-comparison/
```

Purpose:

- compare the minimum product-identification slice
- validate that both input profiles represent the selected identification concepts
- provide the main worked example for documentation and inspection

Start here:

- [examples/03-reduced-use-case-comparison/README.md](../examples/03-reduced-use-case-comparison/README.md)

## Extended Use-Case Comparison

Folder:

```text
examples/04-extended-use-case-comparison/
```

Scope:

```text
battery_passport_metadata_and_classification
```

Purpose:

- validate the same workflow on a broader slice
- add version/revision semantics
- add type/category/classification semantics
- check that the matching and summarization behavior is not overfit to the reduced example

Start here:

- [examples/04-extended-use-case-comparison/README.md](../examples/04-extended-use-case-comparison/README.md)

## Composition Recommendation

Folder:

```text
examples/05-composition-recommendation/
```

Purpose:

- recommend a combined profile from two assessed model sets
- preserve complementary model coverage
- identify declared equivalent entities that need deduplication review
- keep SHACL rewriting outside the automated step

Start here:

- [examples/05-composition-recommendation/README.md](../examples/05-composition-recommendation/README.md)
