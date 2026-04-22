from __future__ import annotations

from collections import defaultdict
from urllib.parse import urlparse

import rdflib
from rdflib import RDF, SH, URIRef

from dpawb.graph import (
    TARGET_PREDICATES,
    ModuleGraph,
    collect_node_shapes,
    collect_property_shapes,
    load_module_graph,
    property_signatures,
)
from dpawb.io import load_yaml_file
from dpawb.metrics import compute_property_metrics, object_reference_targets, overlap_ratio, share
from dpawb.result import build_result
from dpawb.validation import validate_document


def _iri_token(value: str) -> str:
    if "#" in value:
        return value.rsplit("#", 1)[-1]
    return value.rstrip("/").rsplit("/", 1)[-1]


def _collect_vocabulary(module_graph: ModuleGraph) -> set[str]:
    iri_values: set[str] = set()
    for subject, predicate, obj in module_graph.graph:
        for node in (subject, predicate, obj):
            if isinstance(node, URIRef):
                iri_values.add(str(node))
    return iri_values


def _module_resource_index(module_graphs: list[ModuleGraph]) -> dict[str, str]:
    resource_to_module: dict[str, str] = {}
    for module in module_graphs:
        for subject in module.graph.subjects():
            if isinstance(subject, URIRef):
                resource_to_module.setdefault(str(subject), module.model_id)
    return resource_to_module


def _module_for_resource(resource_to_module: dict[str, str], resource_iri: str) -> str | None:
    return resource_to_module.get(resource_iri)


def _metric(metric_id: str, value: float | int, **kwargs: object) -> dict[str, object]:
    payload = {"metric_id": metric_id, "value": value}
    payload.update(kwargs)
    return payload


def _namespace(value: str) -> str:
    if "#" in value:
        return value.rsplit("#", 1)[0] + "#"
    if "/" in value:
        return value.rsplit("/", 1)[0] + "/"
    return value


def _sort_severity(value: str) -> int:
    order = {"high": 1, "medium": 2, "low": 3}
    return order.get(value, 99)


def _is_external_reference(reference: str, known_subjects: set[str], local_namespaces: set[str]) -> bool:
    if reference in known_subjects:
        return False
    parsed = urlparse(reference)
    if parsed.scheme not in {"http", "https"}:
        return False
    return _namespace(reference) not in local_namespaces


def _trace_index(graph: rdflib.Graph) -> dict[str, object]:
    shape_iris = sorted(
        str(shape)
        for shape in collect_node_shapes(graph)
        if isinstance(shape, URIRef)
    )
    property_shape_iris = sorted(
        str(prop)
        for prop in collect_property_shapes(graph)
        if isinstance(prop, URIRef)
    )
    property_path_iris = sorted(
        str(path)
        for prop in collect_property_shapes(graph)
        for path in graph.objects(prop, SH.path)
        if isinstance(path, URIRef)
    )
    class_or_concept_iris = sorted(
        {
            str(obj)
            for predicate in (SH.targetClass, SH["class"])
            for obj in graph.objects(None, predicate)
            if isinstance(obj, URIRef)
        }
    )
    return {
        "shape_iris": shape_iris,
        "property_shape_iris": property_shape_iris,
        "property_path_iris": property_path_iris,
        "class_or_concept_iris": class_or_concept_iris,
    }


def _property_has_type_conflict(graph: rdflib.Graph, prop: rdflib.term.Node) -> bool:
    has_datatype = any(True for _ in graph.objects(prop, SH.datatype))
    has_object_target = any(True for _ in graph.objects(prop, SH["class"]))
    has_object_target = has_object_target or any(True for _ in graph.objects(prop, SH.node))
    has_object_target = has_object_target or any(True for _ in graph.objects(prop, SH.qualifiedValueShape))
    return has_datatype and has_object_target


def assess(profile_path: str) -> dict[str, object]:
    profile = load_yaml_file(profile_path)
    validate_document(profile, "profile", profile_path)

    module_graphs = [
        load_module_graph(model["model_id"], model["source"])
        for model in profile["models"]
    ]
    resource_to_module = _module_resource_index(module_graphs)

    merged_graph = rdflib.Graph()
    for module in module_graphs:
        for triple in module.graph:
            merged_graph.add(triple)

    node_shapes = collect_node_shapes(merged_graph)
    property_shapes = collect_property_shapes(merged_graph)
    total_shapes = len(node_shapes)
    total_property_shapes = len(property_shapes)

    target_declarations = 0
    closed_shapes = 0
    contradictions: list[dict[str, object]] = []
    dangling_references: list[dict[str, object]] = []
    redundancy_candidates: list[dict[str, object]] = []
    known_subjects = {
        str(subject)
        for subject in merged_graph.subjects()
        if isinstance(subject, URIRef)
    }
    local_namespaces = {_namespace(subject) for subject in known_subjects}

    for shape in node_shapes:
        if (shape, SH.closed, rdflib.Literal(True)) in merged_graph:
            closed_shapes += 1
        for predicate in TARGET_PREDICATES:
            target_declarations += sum(1 for _ in merged_graph.objects(shape, predicate))
        for prop_ref in merged_graph.objects(shape, SH.property):
            if not isinstance(prop_ref, URIRef):
                continue
            prop_value = str(prop_ref)
            if _is_external_reference(prop_value, known_subjects, local_namespaces):
                continue
            if prop_value not in known_subjects:
                dangling_references.append(
                    {
                        "finding_id": f"dangling_reference_{len(dangling_references) + 1}",
                        "signal_type": "dangling_reference",
                        "severity": "high",
                        "message": "Node shape references a property shape that cannot be resolved within the composed profile.",
                        "source_reference": {
                            "shape": str(shape),
                            "referenced_iri": prop_value,
                            "module_id": _module_for_resource(resource_to_module, str(shape)),
                        },
                    }
                )

    property_metrics = compute_property_metrics(merged_graph, property_shapes)

    for prop in property_shapes:
        min_count = next(iter(merged_graph.objects(prop, SH.minCount)), None)
        max_count = next(iter(merged_graph.objects(prop, SH.maxCount)), None)
        if min_count is not None and max_count is not None and int(min_count) > int(max_count):
            contradictions.append(
                {
                    "finding_id": f"contradiction_{len(contradictions) + 1}",
                    "signal_type": "contradiction",
                    "severity": "high",
                    "message": "Property shape has min_count greater than max_count.",
                    "source_reference": {
                        "shape": str(prop),
                        "module_id": _module_for_resource(resource_to_module, str(prop)),
                    },
                }
            )
        qualified_min_count = next(iter(merged_graph.objects(prop, SH.qualifiedMinCount)), None)
        qualified_max_count = next(iter(merged_graph.objects(prop, SH.qualifiedMaxCount)), None)
        if (
            qualified_min_count is not None
            and qualified_max_count is not None
            and int(qualified_min_count) > int(qualified_max_count)
        ):
            contradictions.append(
                {
                    "finding_id": f"contradiction_{len(contradictions) + 1}",
                    "signal_type": "contradiction",
                    "severity": "high",
                    "message": "Property shape has qualified_min_count greater than qualified_max_count.",
                    "source_reference": {
                        "shape": str(prop),
                        "module_id": _module_for_resource(resource_to_module, str(prop)),
                    },
                }
            )
        if _property_has_type_conflict(merged_graph, prop):
            contradictions.append(
                {
                    "finding_id": f"contradiction_{len(contradictions) + 1}",
                    "signal_type": "contradiction",
                    "severity": "high",
                    "message": "Property shape mixes literal datatype and object-reference constraints.",
                    "source_reference": {
                        "shape": str(prop),
                        "module_id": _module_for_resource(resource_to_module, str(prop)),
                    },
                }
            )

        for ref in object_reference_targets(merged_graph, prop):
            reference_kind = "object_reference"
            if isinstance(ref, URIRef):
                ref_value = str(ref)
                if _is_external_reference(ref_value, known_subjects, local_namespaces):
                    continue
                if ref_value not in known_subjects:
                    dangling_references.append(
                        {
                            "finding_id": f"dangling_reference_{len(dangling_references) + 1}",
                            "signal_type": "dangling_reference",
                            "severity": "high",
                            "message": f"Referenced {reference_kind} cannot be resolved within the composed profile.",
                            "source_reference": {
                                "shape": str(prop),
                                "referenced_iri": ref_value,
                                "module_id": _module_for_resource(resource_to_module, str(prop)),
                            },
                        }
                    )

    for module in module_graphs:
        for signature, shape_ids in sorted(property_signatures(module.graph).items()):
            if len(shape_ids) < 2 or not any(signature):
                continue
            redundancy_candidates.append(
                {
                    "finding_id": f"redundancy_candidate_{len(redundancy_candidates) + 1}",
                    "signal_type": "redundancy_candidate",
                    "severity": "low",
                    "message": "Near-duplicate property shapes share the same conservative signature.",
                    "source_reference": {"module_id": module.model_id, "property_shapes": sorted(shape_ids)},
                }
            )

    cross_module_reference_count = 0
    for module in module_graphs:
        for prop in collect_property_shapes(module.graph):
            for ref in object_reference_targets(module.graph, prop):
                if resource_to_module.get(str(ref)) not in {None, module.model_id}:
                    cross_module_reference_count += 1

    vocabulary_sets = {module.model_id: _collect_vocabulary(module) for module in module_graphs}
    repeated_iris = set()
    union_iris = set()
    iri_occurrences: defaultdict[str, int] = defaultdict(int)
    for iri_set in vocabulary_sets.values():
        union_iris.update(iri_set)
        for iri in iri_set:
            iri_occurrences[iri] += 1
    repeated_iris = {iri for iri, count in iri_occurrences.items() if count > 1}

    metrics = [
        _metric("number_of_shapes", total_shapes, kind="count"),
        _metric("number_of_property_shapes", total_property_shapes, kind="count"),
        _metric("number_of_target_declarations", target_declarations, kind="count"),
        _metric("number_of_datatype_constrained_properties", property_metrics.datatype_constrained_properties, kind="count"),
        _metric("number_of_object_reference_properties", property_metrics.object_reference_properties, kind="count"),
        _metric("number_of_closed_shapes", closed_shapes, kind="count"),
        _metric(
            "typed_property_share",
            share(property_metrics.typed_properties, total_property_shapes),
            numerator=property_metrics.typed_properties,
            denominator=total_property_shapes,
            kind="share",
        ),
        _metric(
            "cardinality_bounded_property_share",
            share(property_metrics.bounded_properties, total_property_shapes),
            numerator=property_metrics.bounded_properties,
            denominator=total_property_shapes,
            kind="share",
        ),
        _metric(
            "open_property_share",
            share(property_metrics.open_properties, total_property_shapes),
            numerator=property_metrics.open_properties,
            denominator=total_property_shapes,
            kind="share",
        ),
        _metric(
            "constraint_density",
            share(property_metrics.constraint_statement_count, total_property_shapes),
            numerator=property_metrics.constraint_statement_count,
            denominator=total_property_shapes,
            kind="density",
        ),
        _metric("cross_module_reference_count", cross_module_reference_count, kind="count"),
        _metric(
            "cross_module_reference_share",
            share(cross_module_reference_count, property_metrics.object_reference_properties),
            numerator=cross_module_reference_count,
            denominator=property_metrics.object_reference_properties,
            kind="share",
        ),
        _metric("shared_vocabulary_overlap_count", len(repeated_iris), kind="count"),
        _metric(
            "shared_vocabulary_overlap_ratio",
            overlap_ratio(len(repeated_iris), len(union_iris)),
            numerator=len(repeated_iris),
            denominator=len(union_iris),
            kind="share",
        ),
    ]
    metrics = sorted(metrics, key=lambda item: str(item["metric_id"]))

    diagnostics = []
    if not contradictions:
        diagnostics.append(
            {
                "level": "info",
                "message": "Contradiction detection currently covers direct cardinality conflicts and datatype-versus-object-reference conflicts only.",
            }
        )
    diagnostics.append({"level": "info", "message": "Import resolution currently follows explicit owl:imports links only."})
    diagnostics.append(
        {
            "level": "info",
            "message": "Release-1 metric formulas use total property shapes as the denominator for property-based shares and total shapes for shape-based counts.",
        }
    )

    findings = sorted(
        contradictions + dangling_references + redundancy_candidates,
        key=lambda item: (_sort_severity(str(item["severity"])), str(item["finding_id"])),
    )
    inputs = {
        "profile_id": profile["profile_id"],
        "profile_version": profile["profile_version"],
        "comparison_scope_label": profile["comparison_scope_label"],
    }
    content = {
        "profile": {
            "profile_id": profile["profile_id"],
            "label": profile["label"],
            "profile_version": profile["profile_version"],
            "comparison_scope_label": profile["comparison_scope_label"],
            "models": profile["models"],
        },
        "modules": [
            {
                "model_id": module.model_id,
                "source": module.source,
                "source_documents": module.source_documents,
                "node_shape_count": len(collect_node_shapes(module.graph)),
                "property_shape_count": len(collect_property_shapes(module.graph)),
            }
            for module in module_graphs
        ],
        "trace_index": _trace_index(merged_graph),
        "metrics": metrics,
        "maintainability_findings": findings,
    }
    return build_result("assessment_result", inputs, content, diagnostics)
