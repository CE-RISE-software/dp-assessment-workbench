from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

import rdflib
from rdflib import RDF, RDFS, SH, URIRef

from dpawb.graph import collect_node_shapes, collect_property_shapes, load_module_graph
from dpawb.io import load_yaml_file
from dpawb.result import build_result
from dpawb.validation import validate_document


STOPWORDS = {"information", "details", "detail", "or"}


def _normalize(text: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else " " for ch in text).strip()


def _split_identifier_words(text: str) -> set[str]:
    pieces = re.findall(r"[A-Z]+(?=[A-Z][a-z]|[0-9]|\b)|[A-Z]?[a-z]+|[0-9]+", text)
    return {piece.lower() for piece in pieces if piece}


def _tokenize(text: str) -> set[str]:
    normalized = _normalize(text)
    tokens = {token for token in normalized.split() if token}
    for token in list(tokens):
        tokens.update(_split_identifier_words(token))
    tokens.update(_split_identifier_words(text))
    return {token for token in tokens if token and token not in STOPWORDS}


def _local_name(value: str) -> str:
    if "#" in value:
        return value.rsplit("#", 1)[-1]
    return value.rstrip("/").rsplit("/", 1)[-1]


def _node_strings(graph: rdflib.Graph, node: rdflib.term.Node) -> set[str]:
    values = {str(node)}
    if isinstance(node, URIRef):
        values.add(_local_name(str(node)))
    for label in graph.objects(node, RDFS.label):
        values.add(str(label))
    expanded: set[str] = set()
    for value in values:
        if not value:
            continue
        expanded.add(_normalize(value))
        expanded.add(" ".join(sorted(_split_identifier_words(_local_name(value)))))
    return {value.strip() for value in expanded if value.strip()}


@dataclass(slots=True)
class PropertyCandidate:
    property_shape: str
    property_path: str | None
    owner_shapes: list[str]
    owner_target_classes: list[str]
    token_strings: set[str]
    has_datatype: bool
    has_object_reference: bool
    has_node_kind: bool
    has_min_count: bool
    has_max_count: bool
    reference_targets: list[str]


def _build_owner_index(graph: rdflib.Graph) -> dict[str, list[str]]:
    owner_index: dict[str, set[str]] = {}
    for shape in collect_node_shapes(graph):
        if not isinstance(shape, URIRef):
            continue
        owner_shape = str(shape)
        for prop in graph.objects(shape, SH.property):
            owner_index.setdefault(str(prop), set()).add(owner_shape)
    return {key: sorted(value) for key, value in owner_index.items()}


def _owner_target_classes(graph: rdflib.Graph, owner_shapes: list[str]) -> list[str]:
    target_classes: set[str] = set()
    for owner_shape in owner_shapes:
        owner_ref = URIRef(owner_shape)
        for target_class in graph.objects(owner_ref, SH.targetClass):
            if isinstance(target_class, URIRef):
                target_classes.add(str(target_class))
    return sorted(target_classes)


def _build_property_candidates(graph: rdflib.Graph) -> list[PropertyCandidate]:
    owner_index = _build_owner_index(graph)
    candidates: list[PropertyCandidate] = []
    for prop in collect_property_shapes(graph):
        property_shape = str(prop)
        path_node = next(iter(graph.objects(prop, SH.path)), None)
        path_value = str(path_node) if path_node is not None else None
        token_strings = set()
        token_strings.update(_node_strings(graph, prop))
        if path_node is not None:
            token_strings.update(_node_strings(graph, path_node))
        owner_shapes = owner_index.get(property_shape, [])
        owner_target_classes = _owner_target_classes(graph, owner_shapes)
        for owner_shape in owner_shapes:
            token_strings.update(_node_strings(graph, URIRef(owner_shape)))
        for target_class in owner_target_classes:
            token_strings.update(_node_strings(graph, URIRef(target_class)))
        reference_targets = sorted(
            {
                str(ref)
                for predicate in (SH["class"], SH.node, SH.qualifiedValueShape)
                for ref in graph.objects(prop, predicate)
                if isinstance(ref, URIRef)
            }
        )
        candidates.append(
            PropertyCandidate(
                property_shape=property_shape,
                property_path=path_value,
                owner_shapes=owner_shapes,
                owner_target_classes=owner_target_classes,
                token_strings=token_strings,
                has_datatype=any(True for _ in graph.objects(prop, SH.datatype)),
                has_object_reference=any(True for _ in graph.objects(prop, SH["class"]))
                or any(True for _ in graph.objects(prop, SH.node))
                or any(True for _ in graph.objects(prop, SH.qualifiedValueShape)),
                has_node_kind=any(True for _ in graph.objects(prop, SH.nodeKind)),
                has_min_count=any(True for _ in graph.objects(prop, SH.minCount)),
                has_max_count=any(True for _ in graph.objects(prop, SH.maxCount)),
                reference_targets=reference_targets,
            )
        )
    return candidates


def _score_candidate(
    candidate: PropertyCandidate,
    core_required_tokens: set[str],
    expanded_required_tokens: set[str],
) -> tuple[int, int]:
    all_tokens = set()
    for token_string in candidate.token_strings:
        all_tokens.update(_tokenize(token_string))
    overlap = len(expanded_required_tokens.intersection(all_tokens))
    exact = int(bool(core_required_tokens) and core_required_tokens.issubset(all_tokens))
    return exact, overlap


def _core_required_tokens(item: dict[str, object]) -> set[str]:
    item_id = str(item["item_id"])
    label = str(item["label"])
    return _tokenize(label).union(_tokenize(item_id))


def _expanded_required_tokens(item: dict[str, object], core_tokens: set[str]) -> set[str]:
    category = str(item["category"])
    tokens = set(core_tokens)

    if "identifier" in tokens:
        tokens.add("id")
    if "id" in tokens:
        tokens.add("identifier")

    if category == "identification" and "battery" in tokens:
        tokens.add("product")

    if category == "classification" and "battery" in tokens:
        tokens.update({"product", "regulatory", "category"})

    if category == "passport_metadata" and "passport" in tokens:
        tokens.update({"record", "related"})

    if category == "actor" or "manufacturer" in tokens:
        tokens.update({"actor", "operator", "producer", "identifier"})

    return tokens


def _classify_item(item: dict[str, object], candidates: list[PropertyCandidate]) -> dict[str, object]:
    item_id = str(item["item_id"])
    label = str(item["label"])
    core_tokens = _core_required_tokens(item)
    required_tokens = _expanded_required_tokens(item, core_tokens)

    scored_candidates: list[tuple[tuple[int, int], PropertyCandidate]] = []
    for candidate in candidates:
        score = _score_candidate(candidate, core_tokens, required_tokens)
        if score[1] == 0:
            continue
        scored_candidates.append((score, candidate))

    scored_candidates.sort(
        key=lambda entry: (entry[0][0], entry[0][1], len(entry[1].owner_shapes), entry[1].property_shape),
        reverse=True,
    )
    best_candidates = [entry[1] for entry in scored_candidates if entry[0] == scored_candidates[0][0]] if scored_candidates else []

    expects_structured = bool(item.get("expects_structured_value", False))

    if not scored_candidates:
        coverage_class = "not_representable"
        adequacy_note = "No matching property shape was found in the composed SHACL profile."
    elif scored_candidates[0][0][0] == 1 and not expects_structured:
        coverage_class = "representable"
        adequacy_note = "A matching property shape was found through SHACL path and shape tokens."
    elif scored_candidates[0][0][0] == 1 and expects_structured:
        if any(candidate.has_object_reference for candidate in best_candidates):
            coverage_class = "representable"
            adequacy_note = "A matching object-reference property shape supports the expected structured value."
        else:
            coverage_class = "partially_representable"
            adequacy_note = "A matching property shape was found, but structured-value support is weaker than an object reference."
    elif expects_structured and scored_candidates[0][0][1] >= 2:
        coverage_class = "partially_representable"
        adequacy_note = "A plausible structured match was found, but the SHACL evidence remains weaker than a direct object-reference match."
    elif scored_candidates[0][0][1] >= 2:
        coverage_class = "partially_representable"
        adequacy_note = "A plausible property match was found, but the SHACL evidence remains incomplete."
    else:
        coverage_class = "indeterminate"
        adequacy_note = "Only partial SHACL token overlap was found for the required item."

    owner_shapes = sorted({owner for candidate in best_candidates for owner in candidate.owner_shapes})
    owner_target_classes = sorted({target for candidate in best_candidates for target in candidate.owner_target_classes})
    return {
        "finding_id": f"required_item_{item_id}",
        "required_item_id": item_id,
        "coverage_class": coverage_class,
        "category": item["category"],
        "adequacy_note": adequacy_note,
        "supporting_trace": {
            "label": label,
            "matched_property_shapes": [candidate.property_shape for candidate in best_candidates],
            "matched_property_paths": [candidate.property_path for candidate in best_candidates if candidate.property_path],
            "owner_shapes": owner_shapes,
            "owner_target_classes": owner_target_classes,
            "matched_reference_targets": sorted(
                {
                    target
                    for candidate in best_candidates
                    for target in candidate.reference_targets
                }
            ),
        },
    }


def _join_reference_support(
    from_item: dict[str, object],
    to_item: dict[str, object],
    owner_shape_reference_targets: dict[str, set[str]],
) -> bool:
    from_targets = set(from_item["supporting_trace"].get("matched_reference_targets", []))
    to_targets = set(to_item["supporting_trace"].get("matched_reference_targets", []))
    for owner_shape in from_item["supporting_trace"].get("owner_shapes", []):
        from_targets.update(owner_shape_reference_targets.get(owner_shape, set()))
    for owner_shape in to_item["supporting_trace"].get("owner_shapes", []):
        to_targets.update(owner_shape_reference_targets.get(owner_shape, set()))
    from_owner_targets = set(from_item["supporting_trace"].get("owner_target_classes", []))
    to_owner_targets = set(to_item["supporting_trace"].get("owner_target_classes", []))
    return bool(from_targets.intersection(to_owner_targets) or to_targets.intersection(from_owner_targets))


def _record_level_reference_support(
    from_item: dict[str, object],
    to_item: dict[str, object],
) -> bool:
    from_shapes = set(from_item["supporting_trace"].get("owner_shapes", []))
    to_shapes = set(to_item["supporting_trace"].get("owner_shapes", []))
    if from_shapes.intersection(to_shapes):
        return True

    combined_shapes = from_shapes.union(to_shapes)
    product_profile_shapes = {shape for shape in combined_shapes if "product-profile" in shape}
    dp_record_shapes = {shape for shape in combined_shapes if "dp-record-metadata" in shape}
    return bool(product_profile_shapes and (dp_record_shapes or len(product_profile_shapes) >= 2))


def _classify_join(
    join: dict[str, object],
    item_lookup: dict[str, dict[str, object]],
    owner_shape_reference_targets: dict[str, set[str]],
) -> dict[str, object]:
    from_item = item_lookup.get(join["from_item"])
    to_item = item_lookup.get(join["to_item"])
    if not from_item or not to_item:
        coverage_class = "indeterminate"
        note = "Join references an item that is not present in the use-case definition."
        owner_shapes: list[str] = []
    else:
        from_class = from_item["coverage_class"]
        to_class = to_item["coverage_class"]
        if "not_representable" in {from_class, to_class}:
            coverage_class = "not_representable"
            note = "At least one join endpoint is not representable."
            owner_shapes = []
        elif "indeterminate" in {from_class, to_class}:
            coverage_class = "indeterminate"
            note = "At least one join endpoint is indeterminate."
            owner_shapes = []
        else:
            from_shapes = set(from_item["supporting_trace"]["owner_shapes"])
            to_shapes = set(to_item["supporting_trace"]["owner_shapes"])
            shared_shapes = sorted(from_shapes.intersection(to_shapes))
            owner_shapes = shared_shapes
            related_product_profile_shapes = sorted(
                shape
                for shape in from_shapes.union(to_shapes)
                if "product-profile" in shape
            )
            if shared_shapes:
                if from_class == "representable" and to_class == "representable":
                    coverage_class = "representable"
                    note = "Both endpoint items are represented on a shared node shape."
                else:
                    coverage_class = "partially_representable"
                    note = "Both endpoint items can be placed on a shared node shape, but one endpoint remains only partially representable."
            elif _join_reference_support(from_item, to_item, owner_shape_reference_targets):
                if from_class == "representable" and to_class == "representable":
                    coverage_class = "representable"
                    note = "Both endpoint items are connected through an explicit object-reference path between matched owner shapes."
                else:
                    coverage_class = "partially_representable"
                    note = "A cross-shape object-reference path connects the matched items, but one endpoint remains only partially representable."
            elif join.get("join_kind") == "reference" and _record_level_reference_support(from_item, to_item):
                if from_class == "representable" and to_class == "representable":
                    coverage_class = "representable"
                    note = "Both endpoint items appear retrievable from a shared record-level context."
                else:
                    coverage_class = "partially_representable"
                    note = "Both endpoint items appear retrievable from a shared record-level context, but one endpoint remains only partially representable."
            elif join.get("join_kind") == "reference" and len(related_product_profile_shapes) >= 2:
                coverage_class = "partially_representable"
                note = "Both endpoint items were matched in related product-profile structures, but the explicit structural link remains weak."
            else:
                coverage_class = "indeterminate"
                note = "Endpoint items were matched, but no shared owner shape or explicit cross-shape object-reference path was found for the join."

    return {
        "finding_id": f"required_join_{join['join_id']}",
        "required_join_id": join["join_id"],
        "coverage_class": coverage_class,
        "adequacy_note": note,
        "supporting_trace": {
            "from_item": join["from_item"],
            "to_item": join["to_item"],
            "join_kind": join.get("join_kind"),
            "shared_owner_shapes": owner_shapes,
        },
    }


def coverage(profile_path: str, use_case_path: str) -> dict[str, object]:
    profile = load_yaml_file(profile_path)
    use_case = load_yaml_file(use_case_path)
    validate_document(profile, "profile", profile_path)
    validate_document(use_case, "use_case", use_case_path)

    module_graphs = [load_module_graph(model["model_id"], model["source"]) for model in profile["models"]]
    merged_graph = rdflib.Graph()
    for module in module_graphs:
        for triple in module.graph:
            merged_graph.add(triple)

    property_candidates = _build_property_candidates(merged_graph)
    owner_shape_reference_targets: dict[str, set[str]] = {}
    for candidate in property_candidates:
        for owner_shape in candidate.owner_shapes:
            owner_shape_reference_targets.setdefault(owner_shape, set()).update(candidate.reference_targets)
    item_findings = [_classify_item(item, property_candidates) for item in use_case["required_items"]]
    item_findings = sorted(item_findings, key=lambda item: str(item["required_item_id"]))
    item_lookup = {finding["required_item_id"]: finding for finding in item_findings}

    join_findings = [
        _classify_join(join, item_lookup, owner_shape_reference_targets)
        for join in use_case["required_joins"]
    ]
    join_findings = sorted(join_findings, key=lambda item: str(item["required_join_id"]))

    classes = [finding["coverage_class"] for finding in [*item_findings, *join_findings]]
    if any(value == "not_representable" for value in classes):
        overall_class = "not_representable"
    elif any(value == "indeterminate" for value in classes):
        overall_class = "indeterminate"
    elif any(value == "partially_representable" for value in classes):
        overall_class = "partially_representable"
    else:
        overall_class = "representable"

    diagnostics = [
        {
            "level": "info",
            "message": "Coverage matching uses SHACL property-path tokens and owner node-shape evidence for release-1 representability decisions.",
        }
    ]
    inputs = {
        "profile_id": profile["profile_id"],
        "use_case_id": use_case["use_case_id"],
        "comparison_scope_label": profile["comparison_scope_label"],
    }
    content = {
        "profile_id": profile["profile_id"],
        "use_case_id": use_case["use_case_id"],
        "overall_coverage_class": overall_class,
        "required_item_findings": item_findings,
        "required_join_findings": join_findings,
        "source_references": {
            "profile_path": str(Path(profile_path)),
            "use_case_path": str(Path(use_case_path)),
            "model_sources": [model["source"] for model in profile["models"]],
        },
    }
    return build_result("coverage_result", inputs, content, diagnostics)
