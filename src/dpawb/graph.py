from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote, urljoin, urlparse

import rdflib
from rdflib import Graph, OWL, RDF, SH, URIRef

from dpawb.errors import InputError, ProcessingError


TARGET_PREDICATES = {
    SH.targetClass,
    SH.targetNode,
    SH.targetObjectsOf,
    SH.targetSubjectsOf,
}

PROPERTY_CONSTRAINT_PREDICATES = {
    SH.datatype,
    SH["class"],
    SH.node,
    SH.nodeKind,
    SH.minCount,
    SH.maxCount,
    SH.minLength,
    SH.maxLength,
    SH.pattern,
    SH.languageIn,
    SH["in"],
    SH.hasValue,
    SH.qualifiedValueShape,
    SH.qualifiedMinCount,
    SH.qualifiedMaxCount,
}


@dataclass(slots=True)
class ModuleGraph:
    model_id: str
    source: str
    graph: Graph
    source_documents: list[str]


def is_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"}


def is_file_url(value: str) -> bool:
    return urlparse(value).scheme == "file"


def file_url_to_path(value: str) -> Path:
    parsed = urlparse(value)
    return Path(unquote(parsed.path))


def parse_graph(source: str) -> Graph:
    graph = Graph()
    try:
        if is_url(source):
            graph.parse(source, format="turtle")
        elif is_file_url(source):
            graph.parse(file_url_to_path(source), format="turtle")
        else:
            graph.parse(Path(source), format="turtle")
    except Exception as exc:  # noqa: BLE001
        raise InputError(
            f"Unable to load Turtle model source: {source}",
            details=[{"source": source, "error": str(exc)}],
        ) from exc
    return graph


def resolve_import_source(base_source: str, imported_source: str) -> str:
    if is_url(imported_source) or is_file_url(imported_source):
        return imported_source
    if is_url(base_source):
        return urljoin(base_source, imported_source)
    if is_file_url(base_source):
        return str((file_url_to_path(base_source).parent / imported_source).resolve())
    return str((Path(base_source).parent / imported_source).resolve())


def _resolve_imports(source: str, visited: set[str], source_documents: list[str]) -> Graph:
    if source in visited:
        return Graph()
    visited.add(source)
    source_documents.append(source)

    graph = parse_graph(source)
    resolved = Graph()
    for triple in graph:
        resolved.add(triple)

    for imported in sorted(str(obj) for obj in graph.objects(None, OWL.imports)):
        resolved_source = resolve_import_source(source, imported)
        imported_graph = _resolve_imports(resolved_source, visited, source_documents)
        for triple in imported_graph:
            resolved.add(triple)
    return resolved


def load_module_graph(model_id: str, source: str) -> ModuleGraph:
    source_documents: list[str] = []
    graph = _resolve_imports(source, set(), source_documents)
    if len(graph) == 0:
        raise ProcessingError(
            f"Resolved model graph is empty: {source}",
            details=[{"model_id": model_id, "source": source}],
        )
    return ModuleGraph(
        model_id=model_id,
        source=source,
        graph=graph,
        source_documents=sorted(source_documents),
    )


def collect_property_shapes(graph: Graph) -> list[rdflib.term.Node]:
    values = set(graph.subjects(RDF.type, SH.PropertyShape))
    values.update(graph.objects(None, SH.property))
    return sorted(values, key=str)


def collect_node_shapes(graph: Graph) -> list[rdflib.term.Node]:
    values = set(graph.subjects(RDF.type, SH.NodeShape))
    values.difference_update(set(collect_property_shapes(graph)))
    return sorted(values, key=str)


def shape_iris(graph: Graph) -> set[str]:
    values = set()
    for node in collect_node_shapes(graph):
        if isinstance(node, URIRef):
            values.add(str(node))
    return values


def property_signatures(graph: Graph) -> dict[tuple[str, ...], list[str]]:
    signatures: dict[tuple[str, ...], list[str]] = defaultdict(list)
    for prop in collect_property_shapes(graph):
        signature = (
            str(next(iter(graph.objects(prop, SH.path)), "")),
            str(next(iter(graph.objects(prop, SH.datatype)), "")),
            str(next(iter(graph.objects(prop, SH["class"])), "")),
            str(next(iter(graph.objects(prop, SH.node)), "")),
            str(next(iter(graph.objects(prop, SH.minCount)), "")),
            str(next(iter(graph.objects(prop, SH.maxCount)), "")),
        )
        signatures[signature].append(str(prop))
    return signatures
