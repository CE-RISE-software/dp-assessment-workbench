# Digital Passport Model Assessment Workbench

This site documents an agent-oriented analytical toolkit for assessing SHACL-based digital passport models, comparing composed solutions and versions, and checking SHACL-only use-case coverage.

---

## Purpose

The workbench is intended to support open and reproducible analysis of digital passport data models.

It focuses on questions such as:

- how large and structurally complex is a model composition?
- how explicit and constraint-ready is it?
- how do two model compositions or versions differ?
- can a declared use case be represented from the SHACL model alone?
- which findings should be inspected first?

The tool works from inspectable model specifications and declared input files rather than hidden state or representative instance datasets.

## Open Science And Replicability

The analysis is designed to be deterministic:

- the same inputs should produce the same JSON outputs
- input files are explicit and versionable
- result documents are machine-readable and inspectable
- tests use synthetic local fixtures that do not depend on network access
- real live-source examples are separated from validation fixtures

This supports open-science practice: the analytical assumptions, input declarations, result payloads, and example applications can all be reviewed and reproduced.

## Agent-Oriented Use

The workbench is designed to be usable directly by humans, but also by AI agents orchestrating analytical workflows.

The agent-oriented design choices are:

- explicit file-based inputs
- stable package API and CLI operations
- JSON result envelopes
- built-in discovery through `capabilities`, `schema`, `vocabulary`, and `template`
- no chat-specific behavior inside the analytical core

AI agents can therefore help prepare inputs, run the pipeline, inspect outputs, and explain results while the underlying analysis remains deterministic.

## Release-1 Scope

Release 1 provides:

- SHACL ingestion from Turtle sources
- composition-profile assessment
- SHACL-only use-case coverage checks
- pairwise comparison of assessment results
- rule-based prioritization
- discovery of built-in schemas, vocabularies, templates, and capabilities

## Documentation Map

- [Analysis Dimensions](analysis-dimensions.md): what the tool measures and reports.
- [Pipeline](pipeline.md): operations, inputs, outputs, and result documents.
- [API Reference](api-reference.md): Python package functions for humans, agents, and workflow runners.
- [Result Interpretation](result-interpretation.md): how to read rich JSON outputs and deterministic summaries.
- [Example Applications](example-applications.md): tutorial-style analytical progression for humans and AI agents.
- [MCP Server](mcp-server.md): stdio MCP runtime, registry discovery, packaging, and publication shape.
- [Source Ingestion](source-ingestion.md): first tutorial step for profile loading and live URL examples.

## Repository Validation

The repository-native validation path is:

```bash
make validate
```

This runs compile checks, the test suite, and lightweight CLI smoke checks without requiring an editable package install.

---

Funded by the European Union under Grant Agreement No. 101092281 — CE-RISE.  
Views and opinions expressed are those of the author(s) only and do not necessarily reflect those of the European Union or the granting authority (HADEA).
Neither the European Union nor the granting authority can be held responsible for them.

<a href="https://ce-rise.eu/" target="_blank" rel="noopener noreferrer">
  <img src="images/CE-RISE_logo.png" alt="CE-RISE logo" width="200"/>
</a>

© 2026 CE-RISE consortium.  
Licensed under the [European Union Public Licence v1.2 (EUPL-1.2)](https://joinup.ec.europa.eu/collection/eupl/eupl-text-eupl-12).  
Attribution: CE-RISE project (Grant Agreement No. 101092281) and the individual authors/partners as indicated.

<a href="https://www.nilu.com" target="_blank" rel="noopener noreferrer">
  <img src="https://nilu.no/wp-content/uploads/2023/12/nilu-logo-seagreen-rgb-300px.png" alt="NILU logo" height="20"/>
</a>

Developed by NILU (Riccardo Boero — ribo@nilu.no) within the CE-RISE project.
