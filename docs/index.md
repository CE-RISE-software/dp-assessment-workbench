# Digital Passport Model Assessment Workbench

This site documents an agent-oriented analytical toolkit for assessing SHACL-based digital passport models, comparing composed solutions, and checking SHACL-only use-case coverage.

---

## Scope

Release 1 provides:

- SHACL ingestion from Turtle sources
- composition-profile assessment
- SHACL-only use-case coverage checks
- pairwise comparison of assessment results
- rule-based prioritization
- discovery of built-in schemas, vocabularies, templates, and capabilities

## Validation

The repository-native validation path is:

```bash
make validate
```

This runs compile checks, the test suite, and lightweight CLI smoke checks without requiring an editable package install.

## Next

See the [Pipeline](pipeline.md) page for the analytical flow and result documents.

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
