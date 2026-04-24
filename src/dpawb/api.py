from __future__ import annotations

from dpawb.operations.assess import assess as _assess
from dpawb.operations.compare import compare as _compare
from dpawb.operations.coverage import coverage as _coverage
from dpawb.operations.discovery import capabilities as _capabilities
from dpawb.operations.discovery import schema as _schema
from dpawb.operations.discovery import template as _template
from dpawb.operations.discovery import vocabulary as _vocabulary
from dpawb.operations.prioritize import prioritize as _prioritize
from dpawb.operations.summarize import summarize as _summarize


def assess(profile_path: str) -> dict[str, object]:
    """Assess one composition profile and return an ``assessment_result`` document.

    Parameters:
        profile_path: Local path to a composition profile YAML file.

    The profile may contain local SHACL Turtle sources or URL sources. The
    returned dictionary is the canonical JSON-compatible result payload used by
    downstream operations.
    """

    return _assess(profile_path)


def coverage(profile_path: str, use_case_path: str) -> dict[str, object]:
    """Assess SHACL-only use-case coverage for one profile and one use case.

    Parameters:
        profile_path: Local path to a composition profile YAML file.
        use_case_path: Local path to one use-case YAML file.

    Returns a ``coverage_result`` document with required-item findings,
    required-join findings, diagnostics, and trace data.
    """

    return _coverage(profile_path, use_case_path)


def compare(
    left_assessment_path: str,
    right_assessment_path: str,
    alignment_path: str | None = None,
) -> dict[str, object]:
    """Compare exactly two assessment result documents.

    Parameters:
        left_assessment_path: Local path to the left ``assessment_result`` JSON document.
        right_assessment_path: Local path to the right ``assessment_result`` JSON document.
        alignment_path: Optional local path to an analyst-authored alignment YAML file.

    The compared assessments must share the same declared
    ``comparison_scope_label``. Returns a ``comparison_result`` document.
    """

    return _compare(left_assessment_path, right_assessment_path, alignment_path)


def prioritize(
    assessment_path: str,
    comparison_path: str | None = None,
    coverage_paths: list[str] | None = None,
) -> dict[str, object]:
    """Rank improvement targets from existing result documents.

    Parameters:
        assessment_path: Local path to one ``assessment_result`` JSON document.
        comparison_path: Optional local path to one ``comparison_result`` JSON document.
        coverage_paths: Optional list of ``coverage_result`` JSON document paths.

    Returns a deterministic ``prioritization_result`` document.
    """

    return _prioritize(assessment_path, comparison_path, coverage_paths)


def summarize(result_paths: list[str]) -> dict[str, object]:
    """Create a compact deterministic summary from existing result documents.

    Parameters:
        result_paths: One or more local paths to JSON result documents.

    Returns a ``summary_result`` document. This operation is rule-based and does
    not call an AI model.
    """

    return _summarize(result_paths)


def schema(name: str) -> dict[str, object]:
    """Return one bundled JSON Schema as a ``schema_result`` document."""

    return _schema(name)


def vocabulary(name: str) -> dict[str, object]:
    """Return one bundled controlled vocabulary as a ``vocabulary_result`` document."""

    return _vocabulary(name)


def template(name: str) -> dict[str, object]:
    """Return one bundled YAML template as a ``template_result`` document."""

    return _template(name)


def capabilities() -> dict[str, object]:
    """Return command/API capability metadata for humans, agents, and MCP tools."""

    return _capabilities()

__all__ = [
    "assess",
    "coverage",
    "compare",
    "prioritize",
    "schema",
    "vocabulary",
    "template",
    "capabilities",
    "summarize",
]
