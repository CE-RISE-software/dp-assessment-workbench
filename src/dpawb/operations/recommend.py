from __future__ import annotations

import re
from collections import Counter

from dpawb.errors import InputError
from dpawb.io import load_json_file
from dpawb.result import build_result


COVERAGE_CLASS_SCORE = {
    "not_representable": 0,
    "indeterminate": 1,
    "partially_representable": 2,
    "representable": 3,
}


def _require_assessment(document: dict[str, object], path: str) -> None:
    if document.get("result_type") != "assessment_result":
        raise InputError("recommend-composition requires assessment_result inputs", details=[{"path": path}])


def _sanitize_identifier(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9_]+", "_", value.lower())
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    return normalized or "recommended_composition"


def _coverage_summary(coverage_paths: list[str]) -> dict[str, dict[str, object]]:
    summaries: dict[str, dict[str, object]] = {}
    for path in coverage_paths:
        document = load_json_file(path)
        if document.get("result_type") != "coverage_result":
            raise InputError("coverage inputs must be coverage_result documents", details=[{"path": path}])
        profile_id = str(document["inputs"]["profile_id"])
        findings = [
            *document.get("content", {}).get("required_item_findings", []),
            *document.get("content", {}).get("required_join_findings", []),
        ]
        counts = Counter(str(finding.get("coverage_class", "unknown")) for finding in findings)
        score = sum(COVERAGE_CLASS_SCORE.get(str(finding.get("coverage_class")), 0) for finding in findings)
        max_score = len(findings) * max(COVERAGE_CLASS_SCORE.values()) if findings else 0
        summaries[profile_id] = {
            "profile_id": profile_id,
            "use_case_id": document["inputs"].get("use_case_id"),
            "overall_coverage_class": document.get("content", {}).get("overall_coverage_class", "unknown"),
            "finding_count": len(findings),
            "coverage_class_counts": dict(sorted(counts.items())),
            "coverage_score": score,
            "maximum_coverage_score": max_score,
            "coverage_score_ratio": (score / max_score) if max_score else 0.0,
        }
    return summaries


def _profile_coverage_score(profile_id: str, summaries: dict[str, dict[str, object]]) -> float:
    summary = summaries.get(profile_id)
    if not summary:
        return 0.0
    return float(summary.get("coverage_score_ratio", 0.0))


def _module_recommendations(
    assessment: dict[str, object],
    side: str,
    coverage_score: float,
) -> list[dict[str, object]]:
    modules = assessment.get("content", {}).get("modules", [])
    profile_models = {
        str(model["model_id"]): model
        for model in assessment.get("content", {}).get("profile", {}).get("models", [])
    }
    recommendations = []
    for module in modules:
        model_id = str(module["model_id"])
        profile_model = profile_models.get(model_id, {})
        shape_count = int(module.get("node_shape_count", 0))
        property_count = int(module.get("property_shape_count", 0))
        recommendations.append(
            {
                "side": side,
                "model_id": model_id,
                "source": profile_model.get("source", module.get("source")),
                "model_version": profile_model.get("model_version"),
                "action": "include",
                "selection_score": coverage_score + shape_count + property_count,
                "rationale": (
                    "Included to preserve declared model-scope coverage and structural detail in the combined profile."
                ),
                "trace": {
                    "node_shape_count": shape_count,
                    "property_shape_count": property_count,
                    "source_documents": module.get("source_documents", []),
                },
            }
        )
    recommendations.sort(
        key=lambda item: (
            str(item["side"]),
            -float(item["selection_score"]),
            str(item["model_id"]),
        )
    )
    return recommendations


def _unique_model_id(side: str, model_id: str, seen: set[str], duplicate_ids: set[str]) -> str:
    candidate = f"{side}_{model_id}" if model_id in duplicate_ids else model_id
    candidate = _sanitize_identifier(candidate)
    while candidate in seen:
        candidate = f"{candidate}_2"
    seen.add(candidate)
    return candidate


def _candidate_profile(
    left: dict[str, object],
    right: dict[str, object],
    module_recommendations: list[dict[str, object]],
) -> dict[str, object]:
    left_id = str(left["inputs"]["profile_id"])
    right_id = str(right["inputs"]["profile_id"])
    model_counts = Counter(str(item["model_id"]) for item in module_recommendations)
    duplicate_ids = {model_id for model_id, count in model_counts.items() if count > 1}
    seen: set[str] = set()
    models = []
    for item in module_recommendations:
        model = {
            "model_id": _unique_model_id(str(item["side"]), str(item["model_id"]), seen, duplicate_ids),
            "source": item["source"],
        }
        if item.get("model_version"):
            model["model_version"] = item["model_version"]
        models.append(model)
    return {
        "profile_id": _sanitize_identifier(f"recommended_{left_id}_{right_id}"),
        "label": f"Recommended combined profile for {left_id} and {right_id}",
        "profile_version": "recommended",
        "comparison_scope_label": left["inputs"]["comparison_scope_label"],
        "models": models,
    }


def _alignment_recommendations(
    comparison: dict[str, object] | None,
    preferred_side: str,
) -> list[dict[str, object]]:
    if not comparison:
        return []
    alignment = comparison.get("content", {}).get("alignment", {}).get("alignment_aware_comparison")
    if not alignment:
        return []
    recommendations = []
    for pair in alignment.get("evaluated_pairs", []):
        pair_status = str(pair.get("pair_status"))
        if pair_status == "matched":
            action = "deduplicate"
            rationale = (
                f"Declared equivalent entities are present on both sides; keep the {preferred_side} side as canonical "
                "unless domain review shows that the other side carries required detail."
            )
        elif pair_status in {"left_only", "right_only"}:
            action = "retain_unique"
            rationale = "Declared equivalent entity is present on only one side and should be retained for completeness."
        else:
            action = "review"
            rationale = "Declared equivalence could not be matched in either assessment trace."
        recommendations.append(
            {
                "match_id": pair["match_id"],
                "entity_kind": pair["entity_kind"],
                "left_iri": pair["left_iri"],
                "right_iri": pair["right_iri"],
                "pair_status": pair_status,
                "recommended_action": action,
                "preferred_side": preferred_side if action == "deduplicate" else None,
                "rationale": rationale,
            }
        )
    recommendations.sort(
        key=lambda item: (
            {"deduplicate": 0, "retain_unique": 1, "review": 2}.get(str(item["recommended_action"]), 99),
            str(item["match_id"]),
        )
    )
    return recommendations


def recommend_composition(
    left_assessment_path: str,
    right_assessment_path: str,
    comparison_path: str | None = None,
    coverage_paths: list[str] | None = None,
) -> dict[str, object]:
    left = load_json_file(left_assessment_path)
    right = load_json_file(right_assessment_path)
    _require_assessment(left, left_assessment_path)
    _require_assessment(right, right_assessment_path)

    left_scope = left["inputs"]["comparison_scope_label"]
    right_scope = right["inputs"]["comparison_scope_label"]
    if left_scope != right_scope:
        raise InputError(
            "recommend-composition requires matching comparison_scope_label values",
            details=[{"left_scope": left_scope, "right_scope": right_scope}],
        )

    comparison = load_json_file(comparison_path) if comparison_path else None
    if comparison and comparison.get("result_type") != "comparison_result":
        raise InputError("comparison input must be a comparison_result document", details=[{"path": comparison_path}])

    coverage_summaries = _coverage_summary(coverage_paths or [])
    left_id = str(left["inputs"]["profile_id"])
    right_id = str(right["inputs"]["profile_id"])
    left_score = _profile_coverage_score(left_id, coverage_summaries)
    right_score = _profile_coverage_score(right_id, coverage_summaries)
    preferred_side = "right" if right_score > left_score else "left"

    module_recommendations = [
        *_module_recommendations(left, "left", left_score),
        *_module_recommendations(right, "right", right_score),
    ]
    module_recommendations.sort(
        key=lambda item: (
            -float(item["selection_score"]),
            str(item["side"]),
            str(item["model_id"]),
        )
    )
    entity_recommendations = _alignment_recommendations(comparison, preferred_side)
    candidate_profile = _candidate_profile(left, right, module_recommendations)

    review_items = [
        {
            "review_id": f"deduplication_{index + 1}",
            "review_type": "deduplication",
            "message": f"Review declared equivalent entity pair {item['match_id']} before implementing the combined model.",
            "trace": item,
        }
        for index, item in enumerate(entity_recommendations)
        if item["recommended_action"] == "deduplicate"
    ]

    inputs = {
        "left_assessment_path": left_assessment_path,
        "right_assessment_path": right_assessment_path,
        "comparison_path": comparison_path,
        "coverage_paths": coverage_paths or [],
        "comparison_scope_label": left_scope,
    }
    content = {
        "recommendation_strategy": "maximize_declared_coverage_and_structural_detail_with_alignment_deduplication",
        "preferred_side_for_duplicate_entities": preferred_side,
        "coverage_summaries": coverage_summaries,
        "candidate_profile": candidate_profile,
        "module_recommendations": module_recommendations,
        "entity_recommendations": entity_recommendations,
        "review_items": review_items,
    }
    diagnostics = [
        {
            "level": "info",
            "message": "Recommendation is deterministic and does not rewrite SHACL; it emits a proposed profile and review decisions.",
        }
    ]
    return build_result("composition_recommendation_result", inputs, content, diagnostics)
