from __future__ import annotations

from dataclasses import dataclass

import rdflib
from rdflib import SH, URIRef

from dpawb.graph import PROPERTY_CONSTRAINT_PREDICATES


@dataclass(slots=True)
class PropertyMetrics:
    datatype_constrained_properties: int
    object_reference_properties: int
    typed_properties: int
    bounded_properties: int
    open_properties: int
    constraint_statement_count: int


def compute_property_metrics(
    graph: rdflib.Graph,
    property_shapes: list[rdflib.term.Node],
) -> PropertyMetrics:
    datatype_constrained_properties = 0
    object_reference_properties = 0
    typed_properties = 0
    bounded_properties = 0
    open_properties = 0
    constraint_statement_count = 0

    for prop in property_shapes:
        has_datatype = any(True for _ in graph.objects(prop, SH.datatype))
        has_class = any(True for _ in graph.objects(prop, SH["class"]))
        has_node = any(True for _ in graph.objects(prop, SH.node))
        has_qualified_value_shape = any(True for _ in graph.objects(prop, SH.qualifiedValueShape))
        has_node_kind = any(True for _ in graph.objects(prop, SH.nodeKind))
        has_min = any(True for _ in graph.objects(prop, SH.minCount))
        has_max = any(True for _ in graph.objects(prop, SH.maxCount))

        if has_datatype:
            datatype_constrained_properties += 1
        if has_class or has_node or has_qualified_value_shape:
            object_reference_properties += 1
        if has_datatype or has_class or has_node or has_qualified_value_shape or has_node_kind:
            typed_properties += 1
        if has_min or has_max:
            bounded_properties += 1
        if not (has_datatype or has_class or has_node or has_qualified_value_shape or has_node_kind or has_min or has_max):
            open_properties += 1

        for predicate in PROPERTY_CONSTRAINT_PREDICATES:
            constraint_statement_count += sum(1 for _ in graph.objects(prop, predicate))

    return PropertyMetrics(
        datatype_constrained_properties=datatype_constrained_properties,
        object_reference_properties=object_reference_properties,
        typed_properties=typed_properties,
        bounded_properties=bounded_properties,
        open_properties=open_properties,
        constraint_statement_count=constraint_statement_count,
    )


def share(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def overlap_ratio(shared_count: int, union_count: int) -> float:
    if union_count == 0:
        return 0.0
    return shared_count / union_count


def object_reference_targets(graph: rdflib.Graph, prop: rdflib.term.Node) -> list[URIRef]:
    values: list[URIRef] = []
    for predicate in (SH["class"], SH.node, SH.qualifiedValueShape):
        for ref in graph.objects(prop, predicate):
            if isinstance(ref, URIRef):
                values.append(ref)
    return values
