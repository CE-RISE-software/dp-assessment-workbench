from __future__ import annotations

from dpawb.errors import InputError
from dpawb.io import load_json_file
from dpawb.result import build_result


def _coverage_rank(value: str) -> int:
    order = {
        "not_representable": 1,
        "partially_representable": 2,
        "indeterminate": 2,
        "representable": 4,
    }
    return order.get(value, 99)


def _comparison_priority(metric_id: str) -> int | None:
    priority_by_metric = {
        "typed_property_share": 1,
        "cardinality_bounded_property_share": 1,
        "open_property_share": 1,
        "constraint_density": 1,
        "number_of_object_reference_properties": 2,
        "number_of_datatype_constrained_properties": 2,
        "cross_module_reference_share": 3,
        "shared_vocabulary_overlap_ratio": 3,
    }
    return priority_by_metric.get(metric_id)


def prioritize(
    assessment_path: str,
    comparison_path: str | None = None,
    coverage_paths: list[str] | None = None,
) -> dict[str, object]:
    assessment = load_json_file(assessment_path)
    if assessment.get("result_type") != "assessment_result":
        raise InputError("prioritize requires an assessment_result input")

    comparison = None
    if comparison_path:
        comparison = load_json_file(comparison_path)
        if comparison.get("result_type") != "comparison_result":
            raise InputError("prioritize comparison input must be a comparison_result")

    coverage_results = [load_json_file(path) for path in coverage_paths or []]
    for coverage in coverage_results:
        if coverage.get("result_type") != "coverage_result":
            raise InputError("prioritize coverage inputs must all be coverage_result documents")

    targets: list[dict[str, object]] = []
    redundancy_candidates: list[dict[str, object]] = []

    for coverage in coverage_results:
        coverage_findings = []
        coverage_content = coverage.get("content", {})
        coverage_findings.extend(coverage_content.get("required_item_findings", []))
        coverage_findings.extend(coverage_content.get("required_join_findings", []))
        for finding in coverage_findings:
            coverage_class = finding["coverage_class"]
            if coverage_class not in {"not_representable", "partially_representable", "indeterminate"}:
                continue
            finding_ref = finding.get("required_item_id") or finding.get("required_join_id")
            targets.append(
                {
                    "target_id": f"coverage_{finding['finding_id']}",
                    "priority_rank_basis": _coverage_rank(coverage_class),
                    "message": f"Coverage gap for {finding_ref} is {coverage_class}.",
                    "rule_trace": {
                        "rule": coverage_class,
                        "reason": finding["adequacy_note"],
                    },
                }
            )

    for finding in assessment.get("content", {}).get("maintainability_findings", []):
        signal_type = finding["signal_type"]
        if signal_type == "redundancy_candidate":
            redundancy_candidates.append(finding)
            continue
        if signal_type in {"contradiction", "dangling_reference"}:
            rank_basis = 3
        else:
            rank_basis = 6
        targets.append(
            {
                "target_id": f"maintainability_{finding['finding_id']}",
                "priority_rank_basis": rank_basis,
                "message": finding["message"],
                "rule_trace": {
                    "rule": signal_type,
                    "reason": finding["message"],
                },
            }
        )

    if redundancy_candidates:
        targets.append(
            {
                "target_id": "maintainability_redundancy_candidates",
                "priority_rank_basis": 6,
                "message": f"{len(redundancy_candidates)} redundancy candidates were detected across the assessed profile.",
                "rule_trace": {
                    "rule": "redundancy_candidate",
                    "reason": "Near-duplicate property shapes share the same conservative signature.",
                    "count": len(redundancy_candidates),
                },
            }
        )

    if comparison:
        comparison_content = comparison.get("content", {})
        alignment = comparison_content.get("alignment", {}).get("alignment_aware_comparison", {})
        for observation in alignment.get("ranked_alignment_observations", []):
            targets.append(
                {
                    "target_id": f"alignment_{observation['observation_id']}",
                    "priority_rank_basis": 4,
                    "message": observation["message"],
                    "rule_trace": {
                        "rule": "alignment_gap",
                        "reason": observation["message"],
                        "pair_status": observation["pair_status"],
                        "match_id": observation["match_id"],
                    },
                }
            )
        ranked_structural = []
        for observation in comparison_content.get("structural_comparison", {}).get("ranked_observations", []):
            metric_id = str(observation["metric_id"])
            metric_priority = _comparison_priority(metric_id)
            if metric_priority is None:
                continue
            ranked_structural.append((metric_priority, observation))
        ranked_structural.sort(key=lambda item: (item[0], str(item[1]["metric_id"])))
        for _, observation in ranked_structural[:5]:
            targets.append(
                {
                    "target_id": f"comparison_{observation['observation_id']}",
                    "priority_rank_basis": 5,
                    "message": observation["message"],
                    "rule_trace": {
                        "rule": "comparison_delta",
                        "reason": observation["message"],
                    },
                }
            )

    ordered_targets = sorted(
        targets,
        key=lambda item: (int(item["priority_rank_basis"]), str(item["target_id"])),
    )
    for index, target in enumerate(ordered_targets, start=1):
        target["priority_rank"] = index

    inputs = {
        "assessment_profile_id": assessment["inputs"]["profile_id"],
        "comparison_included": bool(comparison),
        "coverage_result_count": len(coverage_results),
    }
    content = {
        "targets": ordered_targets,
    }
    return build_result("prioritization_result", inputs, content, [])
