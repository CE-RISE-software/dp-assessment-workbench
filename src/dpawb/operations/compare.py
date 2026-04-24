from __future__ import annotations

from dpawb.errors import InputError
from dpawb.io import load_json_file, load_yaml_file
from dpawb.result import build_result
from dpawb.validation import validate_document


def _metrics_by_id(document: dict[str, object]) -> dict[str, dict[str, object]]:
    metrics = document.get("content", {}).get("metrics", [])
    return {metric["metric_id"]: metric for metric in metrics}


def _trace_bucket(document: dict[str, object], entity_kind: str) -> set[str]:
    trace_index = document.get("content", {}).get("trace_index", {})
    if entity_kind == "shape":
        return set(trace_index.get("shape_iris", []))
    if entity_kind == "property":
        values = set(trace_index.get("property_path_iris", []))
        values.update(trace_index.get("property_shape_iris", []))
        return values
    if entity_kind == "class_or_concept":
        return set(trace_index.get("class_or_concept_iris", []))
    return set()


def _module_summaries(document: dict[str, object]) -> dict[str, dict[str, object]]:
    summaries: dict[str, dict[str, object]] = {}
    for module in document.get("content", {}).get("modules", []):
        summaries[module["model_id"]] = {
            "model_id": module["model_id"],
            "node_shape_count": module["node_shape_count"],
            "property_shape_count": module["property_shape_count"],
        }
    return summaries


def _ranked_module_deltas(
    left_modules: dict[str, dict[str, object]],
    right_modules: dict[str, dict[str, object]],
) -> list[dict[str, object]]:
    ranked: list[dict[str, object]] = []
    for model_id in sorted(set(left_modules) | set(right_modules)):
        left_module = left_modules.get(model_id, {})
        right_module = right_modules.get(model_id, {})
        left_node_shape_count = int(left_module.get("node_shape_count", 0))
        right_node_shape_count = int(right_module.get("node_shape_count", 0))
        left_property_shape_count = int(left_module.get("property_shape_count", 0))
        right_property_shape_count = int(right_module.get("property_shape_count", 0))
        node_shape_delta = right_node_shape_count - left_node_shape_count
        property_shape_delta = right_property_shape_count - left_property_shape_count
        change_magnitude = abs(node_shape_delta) + abs(property_shape_delta)
        ranked.append(
            {
                "model_id": model_id,
                "left_node_shape_count": left_node_shape_count,
                "right_node_shape_count": right_node_shape_count,
                "node_shape_delta": node_shape_delta,
                "left_property_shape_count": left_property_shape_count,
                "right_property_shape_count": right_property_shape_count,
                "property_shape_delta": property_shape_delta,
                "change_magnitude": change_magnitude,
            }
        )
    ranked.sort(
        key=lambda item: (
            -int(item["change_magnitude"]),
            -abs(int(item["property_shape_delta"])),
            -abs(int(item["node_shape_delta"])),
            str(item["model_id"]),
        )
    )
    return ranked


def _metric_focus(metric_id: str) -> str:
    if "property" in metric_id:
        return "property_shape_count"
    if "shape" in metric_id:
        return "node_shape_count"
    return "overall_change"


def _top_changed_modules_for_metric(
    ranked_module_deltas: list[dict[str, object]],
    metric_id: str,
) -> list[dict[str, object]]:
    focus = _metric_focus(metric_id)
    if focus == "property_shape_count":
        ranked = sorted(
            ranked_module_deltas,
            key=lambda item: (
                -abs(int(item["property_shape_delta"])),
                -abs(int(item["node_shape_delta"])),
                -int(item["change_magnitude"]),
                str(item["model_id"]),
            ),
        )
    elif focus == "node_shape_count":
        ranked = sorted(
            ranked_module_deltas,
            key=lambda item: (
                -abs(int(item["node_shape_delta"])),
                -abs(int(item["property_shape_delta"])),
                -int(item["change_magnitude"]),
                str(item["model_id"]),
            ),
        )
    else:
        ranked = ranked_module_deltas
    return ranked[:3]


def _direction(delta: float) -> str:
    return "increased" if delta > 0 else "decreased"


def _comparison_signal_priority(metric_id: str, kind: str | None) -> int:
    if kind in {"share", "density"}:
        return 1
    if metric_id in {"cross_module_reference_count", "shared_vocabulary_overlap_count"}:
        return 2
    return 3


def _normalized_delta_score(left_value: float, right_value: float, kind: str | None) -> float:
    delta = right_value - left_value
    if kind in {"share", "density"}:
        return abs(delta)
    scale = max(abs(left_value), abs(right_value), 1.0)
    return abs(delta) / scale


def _observation_message(metric_id: str, delta: float) -> str:
    direction = _direction(delta)
    absolute_delta = abs(delta)
    if metric_id in {"number_of_shapes", "number_of_property_shapes", "number_of_target_declarations"}:
        return f"{metric_id} {direction} by {absolute_delta}, indicating structural expansion or contraction."
    if metric_id in {
        "number_of_datatype_constrained_properties",
        "number_of_closed_shapes",
        "number_of_object_reference_properties",
    }:
        return f"{metric_id} {direction} by {absolute_delta}, suggesting a shift in modelling explicitness."
    if metric_id in {"typed_property_share", "cardinality_bounded_property_share", "constraint_density"}:
        qualifier = "stronger explicitness" if delta > 0 else "weaker explicitness"
        return f"{metric_id} {direction} by {absolute_delta}, suggesting {qualifier}."
    if metric_id in {"open_property_share"}:
        qualifier = "more open modelling" if delta > 0 else "less open modelling"
        return f"{metric_id} {direction} by {absolute_delta}, suggesting {qualifier}."
    if metric_id in {"cross_module_reference_count", "cross_module_reference_share"}:
        qualifier = "stronger modular coupling" if delta > 0 else "weaker modular coupling"
        return f"{metric_id} {direction} by {absolute_delta}, suggesting {qualifier}."
    if metric_id in {"shared_vocabulary_overlap_count", "shared_vocabulary_overlap_ratio"}:
        qualifier = "more vocabulary reuse" if delta > 0 else "less vocabulary reuse"
        return f"{metric_id} {direction} by {absolute_delta}, suggesting {qualifier}."
    return f"{metric_id} {direction} by {absolute_delta}."


def _alignment_pair_status(left_present: bool, right_present: bool) -> str:
    if left_present and right_present:
        return "matched"
    if left_present:
        return "left_only"
    if right_present:
        return "right_only"
    return "missing_both"


def _alignment_observation_message(pair_status: str, match_id: str) -> str:
    if pair_status == "left_only":
        return f"{match_id} is declared equivalent but only the left-side entity is present."
    if pair_status == "right_only":
        return f"{match_id} is declared equivalent but only the right-side entity is present."
    if pair_status == "missing_both":
        return f"{match_id} is declared equivalent but neither side is present in the compared traces."
    return f"{match_id} is declared equivalent and matched on both sides."


def _alignment_review_priority(pair_status: str) -> int:
    if pair_status == "left_only":
        return 1
    if pair_status == "right_only":
        return 2
    if pair_status == "missing_both":
        return 3
    return 4


def compare(left_path: str, right_path: str, alignment_path: str | None = None) -> dict[str, object]:
    left = load_json_file(left_path)
    right = load_json_file(right_path)
    if left.get("result_type") != "assessment_result" or right.get("result_type") != "assessment_result":
        raise InputError("compare requires exactly two assessment_result inputs")

    left_scope = left["inputs"]["comparison_scope_label"]
    right_scope = right["inputs"]["comparison_scope_label"]
    if left_scope != right_scope:
        raise InputError(
            "Assessment results cannot be compared because comparison_scope_label does not match",
            details=[{"left_scope": left_scope, "right_scope": right_scope}],
        )

    left_metrics = _metrics_by_id(left)
    right_metrics = _metrics_by_id(right)
    metric_ids = sorted(set(left_metrics) | set(right_metrics))
    metric_deltas = []
    for metric_id in metric_ids:
        left_metric = left_metrics.get(metric_id)
        right_metric = right_metrics.get(metric_id)
        left_value = float(left_metric["value"]) if left_metric else 0.0
        right_value = float(right_metric["value"]) if right_metric else 0.0
        kind = str(left_metric.get("kind") if left_metric else right_metric.get("kind")) if (left_metric or right_metric) else None
        metric_deltas.append(
            {
                "metric_id": metric_id,
                "left_value": left_value,
                "right_value": right_value,
                "delta": right_value - left_value,
                "kind": kind,
                "normalized_delta_score": _normalized_delta_score(left_value, right_value, kind),
            }
        )

    ranked_observations = [
        {
            "observation_id": f"metric_delta_{index + 1}",
            "message": _observation_message(str(item["metric_id"]), float(item["delta"])),
            "metric_id": item["metric_id"],
            "delta": item["delta"],
            "kind": item.get("kind"),
            "normalized_delta_score": item["normalized_delta_score"],
        }
        for index, item in enumerate(
            sorted(
                metric_deltas,
                key=lambda entry: (
                    _comparison_signal_priority(str(entry["metric_id"]), entry.get("kind")),
                    -float(entry["normalized_delta_score"]),
                    -abs(float(entry["delta"])),
                    str(entry["metric_id"]),
                ),
            )
        )
        if float(item["delta"]) != 0.0
    ]

    left_modules = _module_summaries(left)
    right_modules = _module_summaries(right)
    ranked_module_deltas = _ranked_module_deltas(left_modules, right_modules)
    for observation in ranked_observations:
        metric_id = str(observation["metric_id"])
        observation["module_context"] = {
            "metric_focus": _metric_focus(metric_id),
            "change_basis": "node_shape_count_and_property_shape_count",
            "top_changed_modules": _top_changed_modules_for_metric(ranked_module_deltas, metric_id),
        }

    inputs = {
        "left_profile_id": left["inputs"]["profile_id"],
        "right_profile_id": right["inputs"]["profile_id"],
        "comparison_scope_label": left_scope,
    }
    content = {
        "structural_comparison": {
            "metric_deltas": metric_deltas,
            "ranked_observations": ranked_observations,
        },
    }

    if alignment_path:
        alignment = load_yaml_file(alignment_path)
        validate_document(alignment, "alignment", alignment_path)
        alignment_scope = alignment["comparison_scope_label"]
        if alignment_scope != left_scope:
            raise InputError(
                "Alignment file comparison_scope_label does not match the compared assessment results",
                details=[{"alignment_scope": alignment_scope, "comparison_scope_label": left_scope}],
            )
        left_matches = 0
        right_matches = 0
        bilateral_matches = 0
        evaluated_pairs = []
        for equivalence in alignment["equivalences"]:
            left_bucket = _trace_bucket(left, equivalence["entity_kind"])
            right_bucket = _trace_bucket(right, equivalence["entity_kind"])
            left_present = equivalence["left_iri"] in left_bucket
            right_present = equivalence["right_iri"] in right_bucket
            if left_present:
                left_matches += 1
            if right_present:
                right_matches += 1
            if left_present and right_present:
                bilateral_matches += 1
            pair_status = _alignment_pair_status(left_present, right_present)
            evaluated_pairs.append(
                {
                    "match_id": equivalence["match_id"],
                    "entity_kind": equivalence["entity_kind"],
                    "left_iri": equivalence["left_iri"],
                    "right_iri": equivalence["right_iri"],
                    "left_present": left_present,
                    "right_present": right_present,
                    "pair_status": pair_status,
                }
            )

        equivalence_count = len(alignment["equivalences"])
        ranked_alignment_observations = [
            {
                "observation_id": f"alignment_gap_{index + 1}",
                "match_id": pair["match_id"],
                "entity_kind": pair["entity_kind"],
                "pair_status": pair["pair_status"],
                "message": _alignment_observation_message(str(pair["pair_status"]), str(pair["match_id"])),
            }
            for index, pair in enumerate(
                sorted(
                    (
                        pair
                        for pair in evaluated_pairs
                        if str(pair["pair_status"]) != "matched"
                    ),
                    key=lambda pair: (
                        _alignment_review_priority(str(pair["pair_status"])),
                        str(pair["match_id"]),
                    ),
                )
            )
        ]
        content["alignment"] = {
            "alignment_id": alignment["alignment_id"],
            "comparison_scope_label": alignment_scope,
            "equivalence_count": equivalence_count,
            "alignment_aware_comparison": {
                "status": "declared_alignment_evaluated",
                "matched_pair_count": bilateral_matches,
                "left_present_count": left_matches,
                "right_present_count": right_matches,
                "alignment_coverage_ratio": (bilateral_matches / equivalence_count) if equivalence_count else 0.0,
                "evaluated_pairs": evaluated_pairs,
                "ranked_alignment_observations": ranked_alignment_observations,
            },
        }
    return build_result("comparison_result", inputs, content, [])
