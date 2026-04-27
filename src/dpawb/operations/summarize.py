from __future__ import annotations

from collections import Counter
from pathlib import Path

from dpawb.io import load_json_file
from dpawb.result import build_result


TOP_N_SIGNALS = 3
COVERAGE_CLASS_ORDER = {
    "not_representable": 0,
    "indeterminate": 1,
    "partially_representable": 2,
    "representable": 3,
}


def _coverage_points(document: dict[str, object]) -> list[str]:
    content = document.get("content", {})
    overall = content.get("overall_coverage_class", "unknown")
    points = [f"Coverage overall is {overall}."]
    findings = [
        *content.get("required_item_findings", []),
        *content.get("required_join_findings", []),
    ]
    counter = Counter(str(finding.get("coverage_class", "unknown")) for finding in findings)
    for coverage_class in sorted(counter, key=lambda value: COVERAGE_CLASS_ORDER.get(value, 99)):
        points.append(f"{counter[coverage_class]} coverage finding(s) are {coverage_class}.")
    promoted = [
        finding for finding in findings
        if finding.get("coverage_class") != "representable"
    ]
    promoted.sort(
        key=lambda finding: (
            COVERAGE_CLASS_ORDER.get(str(finding.get("coverage_class")), 99),
            str(finding.get("required_item_id") or finding.get("required_join_id")),
        )
    )
    for finding in promoted[:TOP_N_SIGNALS]:
        finding_ref = finding.get("required_item_id") or finding.get("required_join_id")
        points.append(f"Coverage follow-up: {finding_ref} is {finding['coverage_class']}.")
    return points


def _comparison_points(document: dict[str, object]) -> list[str]:
    content = document.get("content", {})
    structural = content.get("structural_comparison", {})
    observations = structural.get("ranked_observations", [])
    points: list[str] = []
    if observations:
        for observation in observations[:TOP_N_SIGNALS]:
            points.append(f"Comparison signal: {observation['metric_id']}: {observation['message']}")
    alignment = content.get("alignment", {}).get("alignment_aware_comparison")
    if alignment:
        ratio = alignment.get("alignment_coverage_ratio", 0)
        matched = alignment.get("matched_pair_count", 0)
        points.append(f"Declared alignment coverage is {ratio} with {matched} matched pair(s).")
        gaps = alignment.get("ranked_alignment_observations", [])
        if gaps:
            points.append(f"{len(gaps)} declared alignment gap(s) need review.")
            for gap in gaps[:TOP_N_SIGNALS]:
                points.append(f"Alignment follow-up: {gap['message']}")
    return points or ["Comparison result contains no ranked observations."]


def _prioritization_points(document: dict[str, object]) -> list[str]:
    targets = document.get("content", {}).get("targets", [])
    if not targets:
        return ["No prioritization targets were emitted."]
    top = targets[0]
    points = [f"{len(targets)} prioritization target(s) were emitted."]
    for target in targets[:TOP_N_SIGNALS]:
        points.append(f"Priority {target['priority_rank']}: {target['target_id']}: {target['message']}")
    return points


def _composition_recommendation_points(document: dict[str, object]) -> list[str]:
    content = document.get("content", {})
    profile = content.get("candidate_profile", {})
    modules = content.get("module_recommendations", [])
    entities = content.get("entity_recommendations", [])
    review_items = content.get("review_items", [])
    points = [
        f"Recommended candidate profile is {profile.get('profile_id', 'unknown')}.",
        f"{len(modules)} module recommendation(s) and {len(entities)} entity recommendation(s) were emitted.",
    ]
    if review_items:
        points.append(f"{len(review_items)} deduplication review item(s) need inspection before implementation.")
    return points


def _assessment_points(document: dict[str, object]) -> list[str]:
    content = document.get("content", {})
    metrics = content.get("metrics", [])
    findings = content.get("maintainability_findings", [])
    modules = content.get("modules", [])
    points = [
        f"Assessment contains {len(metrics)} metric(s) across {len(modules)} module(s).",
        f"Assessment reports {len(findings)} maintainability finding(s).",
    ]
    metric_lookup = {metric["metric_id"]: metric for metric in metrics}
    for metric_id in ("number_of_shapes", "number_of_property_shapes", "typed_property_share"):
        if metric_id in metric_lookup:
            points.append(f"{metric_id} = {metric_lookup[metric_id]['value']}.")
    return points


def _points_for_document(document: dict[str, object]) -> list[str]:
    result_type = document.get("result_type")
    if result_type == "assessment_result":
        return _assessment_points(document)
    if result_type == "coverage_result":
        return _coverage_points(document)
    if result_type == "comparison_result":
        return _comparison_points(document)
    if result_type == "prioritization_result":
        return _prioritization_points(document)
    if result_type == "composition_recommendation_result":
        return _composition_recommendation_points(document)
    return [f"Unsupported result type for detailed summarization: {result_type}."]


def _headline(result_types: list[str], key_points: list[str]) -> str:
    if "coverage_result" in result_types and all("Coverage overall is representable." not in point for point in key_points):
        return "At least one coverage result is not fully representable."
    if "coverage_result" in result_types and "comparison_result" in result_types:
        return "Coverage and comparison results are available for interpretation."
    if "comparison_result" in result_types:
        return "Comparison results are available for interpretation."
    if "composition_recommendation_result" in result_types:
        return "Composition recommendation results are available for interpretation."
    if "assessment_result" in result_types:
        return "Assessment results are available for interpretation."
    return "Result documents were summarized."


def summarize(result_paths: list[str]) -> dict[str, object]:
    documents = [load_json_file(path) for path in result_paths]
    result_types = [str(document.get("result_type", "unknown")) for document in documents]
    key_points: list[str] = []
    for path, document in zip(result_paths, documents, strict=True):
        for point in _points_for_document(document):
            key_points.append(f"{Path(path).name}: {point}")

    content = {
        "headline": _headline(result_types, key_points),
        "result_types": result_types,
        "key_points": key_points,
        "follow_up_questions": [
            "Which findings should be promoted into a human-readable report?",
            "Do the declared comparison scope and alignment still match the analytical intent?",
        ],
    }
    inputs = {
        "result_count": len(result_paths),
        "result_paths": result_paths,
    }
    return build_result("summary_result", inputs, content, [])


def render_markdown(summary_result: dict[str, object]) -> str:
    content = summary_result["content"]
    lines = [
        "# Summary",
        "",
        str(content["headline"]),
        "",
        "## Key Points",
        "",
    ]
    lines.extend(f"- {point}" for point in content.get("key_points", []))
    follow_up_questions = content.get("follow_up_questions", [])
    if follow_up_questions:
        lines.extend(["", "## Follow-Up Questions", ""])
        lines.extend(f"- {question}" for question in follow_up_questions)
    lines.append("")
    return "\n".join(lines)
