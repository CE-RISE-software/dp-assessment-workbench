from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import rdflib
import yaml
from jsonschema import Draft202012Validator

from dpawb.api import assess, capabilities, compare, coverage, prioritize, schema, summarize, template, vocabulary
from dpawb.operations.coverage import PropertyCandidate, _classify_item, _classify_join
from dpawb.operations.summarize import render_markdown


FIXTURES = Path("fixtures")
EXAMPLES = Path("examples")


class PipelineTests(unittest.TestCase):
    def test_capabilities_enumerates_contract_surface(self) -> None:
        result = capabilities()
        self.assertEqual(result["result_type"], "capabilities_result")
        self.assertIn("inputs", result)
        self.assertIn("content", result)
        commands = result["content"]["commands"]
        self.assertIn("assess", [item["command"] for item in commands])
        assess_command = next(item for item in commands if item["command"] == "assess")
        self.assertEqual(assess_command["api_function"], "assess")
        self.assertEqual(assess_command["mcp_tool"], "assess")
        self.assertIn("profile", assess_command["input_fields"])
        self.assertIn("alignment", result["content"]["schemas"])
        self.assertIn("summarize", [item["command"] for item in commands])
        self.assertIn("summary_result", result["content"]["schemas"])

    def test_assess_latest_fixture_returns_metrics(self) -> None:
        result = assess(str(FIXTURES / "profiles" / "synthetic_evolution_latest.yaml"))
        self.assertEqual(result["result_type"], "assessment_result")
        self.assertIn("inputs", result)
        self.assertIn("content", result)
        metrics = {metric["metric_id"]: metric for metric in result["content"]["metrics"]}
        self.assertEqual(metrics["number_of_property_shapes"]["value"], 3)
        self.assertEqual(metrics["number_of_object_reference_properties"]["value"], 1)
        self.assertEqual(metrics["number_of_closed_shapes"]["value"], 1)
        self.assertEqual(metrics["cardinality_bounded_property_share"]["numerator"], 3)
        self.assertEqual(metrics["cardinality_bounded_property_share"]["denominator"], 3)
        self.assertEqual(metrics["typed_property_share"]["value"], 1.0)
        self.assertEqual(metrics["cross_module_reference_share"]["value"], 0.0)

    def test_assess_resolves_relative_imports(self) -> None:
        result = assess(str(FIXTURES / "profiles" / "synthetic_import_profile.yaml"))
        module = result["content"]["modules"][0]
        self.assertGreaterEqual(module["node_shape_count"], 1)
        self.assertEqual(len(module["source_documents"]), 2)

    def test_assess_reports_dangling_references(self) -> None:
        result = assess(str(FIXTURES / "profiles" / "synthetic_dangling_profile.yaml"))
        dangling_findings = [
            finding for finding in result["content"]["maintainability_findings"]
            if finding["signal_type"] == "dangling_reference"
        ]
        self.assertGreaterEqual(len(dangling_findings), 1)
        self.assertEqual(dangling_findings[0]["source_reference"]["module_id"], "broken_module")

    def test_assess_reports_missing_property_shape_reference(self) -> None:
        result = assess(str(FIXTURES / "profiles" / "synthetic_missing_property_shape_profile.yaml"))
        messages = [finding["message"] for finding in result["content"]["maintainability_findings"]]
        self.assertIn(
            "Node shape references a property shape that cannot be resolved within the composed profile.",
            messages,
        )

    def test_assess_reports_direct_contradictions(self) -> None:
        result = assess(str(FIXTURES / "profiles" / "synthetic_contradiction_profile.yaml"))
        contradiction_findings = [
            finding for finding in result["content"]["maintainability_findings"]
            if finding["signal_type"] == "contradiction"
        ]
        self.assertGreaterEqual(len(contradiction_findings), 1)
        self.assertEqual(contradiction_findings[0]["source_reference"]["module_id"], "contradictory_module")

    def test_assess_reports_richer_direct_contradictions(self) -> None:
        result = assess(str(FIXTURES / "profiles" / "synthetic_richer_contradiction_profile.yaml"))
        contradiction_messages = {
            finding["message"]
            for finding in result["content"]["maintainability_findings"]
            if finding["signal_type"] == "contradiction"
        }
        self.assertIn("Property shape mixes literal datatype and object-reference constraints.", contradiction_messages)
        self.assertIn("Property shape has qualified_min_count greater than qualified_max_count.", contradiction_messages)

    def test_assess_reports_redundancy_candidates(self) -> None:
        result = assess(str(FIXTURES / "profiles" / "synthetic_redundancy_profile.yaml"))
        signal_types = {finding["signal_type"] for finding in result["content"]["maintainability_findings"]}
        self.assertIn("redundancy_candidate", signal_types)

    def test_coverage_and_prioritize_round_trip(self) -> None:
        assessment_result = assess(str(FIXTURES / "profiles" / "synthetic_evolution_latest.yaml"))
        coverage_result = coverage(
            str(FIXTURES / "profiles" / "synthetic_evolution_latest.yaml"),
            str(FIXTURES / "use_cases" / "version_identity_lookup.yaml"),
        )
        self.assertEqual(coverage_result["result_type"], "coverage_result")
        self.assertEqual(coverage_result["content"]["overall_coverage_class"], "not_representable")
        with tempfile.TemporaryDirectory() as tmpdir:
            assessment_path = Path(tmpdir) / "assessment.json"
            coverage_path = Path(tmpdir) / "coverage.json"
            assessment_path.write_text(json.dumps(assessment_result), encoding="utf-8")
            coverage_path.write_text(json.dumps(coverage_result), encoding="utf-8")
            prioritization = prioritize(str(assessment_path), coverage_paths=[str(coverage_path)])
        self.assertEqual(prioritization["result_type"], "prioritization_result")
        self.assertGreaterEqual(len(prioritization["content"]["targets"]), 1)

    def test_coverage_marks_identity_join_representable_when_items_share_shape(self) -> None:
        coverage_result = coverage(
            str(FIXTURES / "profiles" / "synthetic_evolution_latest.yaml"),
            str(FIXTURES / "use_cases" / "product_identity_lookup.yaml"),
        )
        self.assertEqual(coverage_result["content"]["overall_coverage_class"], "representable")
        join_finding = coverage_result["content"]["required_join_findings"][0]
        self.assertEqual(join_finding["coverage_class"], "representable")

    def test_coverage_matches_camel_case_property_paths(self) -> None:
        coverage_result = coverage(
            str(FIXTURES / "profiles" / "synthetic_camel_case_profile.yaml"),
            str(FIXTURES / "use_cases" / "record_metadata_lookup.yaml"),
        )
        self.assertEqual(coverage_result["content"]["overall_coverage_class"], "representable")
        item_finding = coverage_result["content"]["required_item_findings"][0]
        self.assertEqual(item_finding["coverage_class"], "representable")

    def test_semantic_aliases_mark_battery_identifier_representable(self) -> None:
        item = {
            "item_id": "battery_identifier",
            "label": "Battery identifier",
            "category": "identification",
            "expects_structured_value": False,
        }
        candidate = PropertyCandidate(
            property_shape="shape_1",
            property_path="https://example.org/unique_product_identifier_value",
            owner_shapes=["https://example.org/uniqueProductIdentifier"],
            owner_target_classes=["https://example.org/uniqueProductIdentifier"],
            token_strings={"unique product identifier value", "uniqueProductIdentifier"},
            has_datatype=True,
            has_object_reference=False,
            has_node_kind=False,
            has_min_count=True,
            has_max_count=True,
            reference_targets=[],
        )
        finding = _classify_item(item, [candidate])
        self.assertEqual(finding["coverage_class"], "representable")

    def test_structured_owner_context_marks_battery_category_representable(self) -> None:
        item = {
            "item_id": "battery_category",
            "label": "Battery category",
            "category": "classification",
            "expects_structured_value": True,
        }
        candidate = PropertyCandidate(
            property_shape="shape_2",
            property_path="https://example.org/product_category_value",
            owner_shapes=["https://example.org/regulatoryClassification"],
            owner_target_classes=["https://example.org/regulatoryClassification"],
            token_strings={"product category value", "regulatory classification"},
            has_datatype=True,
            has_object_reference=False,
            has_node_kind=False,
            has_min_count=False,
            has_max_count=False,
            reference_targets=[],
        )
        finding = _classify_item(item, [candidate])
        self.assertEqual(finding["coverage_class"], "representable")

    def test_version_revision_semantics_mark_version_item_representable(self) -> None:
        item = {
            "item_id": "passport_version_or_revision",
            "label": "Passport version or revision",
            "category": "versioning_provenance",
            "expects_structured_value": False,
        }
        candidate = PropertyCandidate(
            property_shape="shape_3",
            property_path="http://purl.org/pav/version",
            owner_shapes=["https://example.org/RelatedPassport"],
            owner_target_classes=["https://example.org/RelatedPassport"],
            token_strings={"version", "RelatedPassport"},
            has_datatype=True,
            has_object_reference=False,
            has_node_kind=False,
            has_min_count=True,
            has_max_count=True,
            reference_targets=[],
        )
        finding = _classify_item(item, [candidate])
        self.assertEqual(finding["coverage_class"], "representable")

    def test_type_category_semantics_mark_classification_item_representable(self) -> None:
        item = {
            "item_id": "battery_type_or_classification",
            "label": "Battery type or classification",
            "category": "classification",
            "expects_structured_value": True,
        }
        candidate = PropertyCandidate(
            property_shape="shape_4",
            property_path="https://example.org/product_category_value",
            owner_shapes=["https://example.org/regulatoryClassification"],
            owner_target_classes=["https://example.org/regulatoryClassification"],
            token_strings={"product category value", "regulatory classification"},
            has_datatype=True,
            has_object_reference=False,
            has_node_kind=False,
            has_min_count=False,
            has_max_count=False,
            reference_targets=[],
        )
        finding = _classify_item(item, [candidate])
        self.assertEqual(finding["coverage_class"], "representable")

    def test_record_level_provenance_join_is_representable_with_shared_dp_record_context(self) -> None:
        item_lookup = {
            "passport_identifier": {
                "coverage_class": "representable",
                "supporting_trace": {
                    "owner_shapes": ["https://example.org/dp-record-metadata/RelatedPassport"],
                    "owner_target_classes": [],
                    "matched_reference_targets": [],
                },
            },
            "passport_version_or_revision": {
                "coverage_class": "representable",
                "supporting_trace": {
                    "owner_shapes": ["http://rdfs.org/ns/void#Dataset"],
                    "owner_target_classes": [],
                    "matched_reference_targets": [],
                },
            },
        }
        join = {
            "join_id": "passport_to_version",
            "from_item": "passport_identifier",
            "to_item": "passport_version_or_revision",
            "join_kind": "provenance",
        }
        finding = _classify_join(join, item_lookup, {})
        self.assertEqual(finding["coverage_class"], "representable")

    def test_coverage_marks_cross_shape_reference_join_representable(self) -> None:
        coverage_result = coverage(
            str(FIXTURES / "profiles" / "synthetic_reference_join_profile.yaml"),
            str(FIXTURES / "use_cases" / "passport_actor_lookup.yaml"),
        )
        self.assertEqual(coverage_result["content"]["overall_coverage_class"], "representable")
        join_finding = coverage_result["content"]["required_join_findings"][0]
        self.assertEqual(join_finding["coverage_class"], "representable")
        self.assertIn("explicit object-reference path", join_finding["adequacy_note"])

    def test_compare_validates_alignment_scope(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            left = assess(str(FIXTURES / "profiles" / "synthetic_solution_a.yaml"))
            right = assess(str(FIXTURES / "profiles" / "synthetic_solution_b.yaml"))
            left_path = Path(tmpdir) / "left.json"
            right_path = Path(tmpdir) / "right.json"
            left_path.write_text(json.dumps(left), encoding="utf-8")
            right_path.write_text(json.dumps(right), encoding="utf-8")
            result = compare(
                str(left_path),
                str(right_path),
                str(FIXTURES / "alignments" / "synthetic_solution_alignment.yaml"),
            )
        self.assertEqual(result["result_type"], "comparison_result")
        self.assertIn("inputs", result)
        self.assertIn("content", result)
        observation = result["content"]["structural_comparison"]["ranked_observations"][0]
        self.assertIn("module_context", observation)
        self.assertIn("suggesting", observation["message"])
        self.assertEqual(
            observation["module_context"]["change_basis"],
            "node_shape_count_and_property_shape_count",
        )
        self.assertIn("metric_focus", observation["module_context"])
        self.assertIn("top_changed_modules", observation["module_context"])
        self.assertGreaterEqual(len(observation["module_context"]["top_changed_modules"]), 1)
        alignment = result["content"]["alignment"]["alignment_aware_comparison"]
        self.assertEqual(alignment["status"], "declared_alignment_evaluated")
        self.assertEqual(alignment["matched_pair_count"], 2)
        self.assertEqual(alignment["alignment_coverage_ratio"], 1.0)
        self.assertIn("ranked_alignment_observations", alignment)
        self.assertEqual(alignment["ranked_alignment_observations"], [])

    def test_compare_prioritizes_normalized_signals_over_raw_size_deltas(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            left = assess(str(FIXTURES / "profiles" / "synthetic_solution_a.yaml"))
            right = assess(str(FIXTURES / "profiles" / "synthetic_solution_b.yaml"))
            left_path = Path(tmpdir) / "left.json"
            right_path = Path(tmpdir) / "right.json"
            left_path.write_text(json.dumps(left), encoding="utf-8")
            right_path.write_text(json.dumps(right), encoding="utf-8")
            result = compare(str(left_path), str(right_path))

        first_metric = result["content"]["structural_comparison"]["ranked_observations"][0]["metric_id"]
        self.assertIn(
            first_metric,
            {
                "typed_property_share",
                "cardinality_bounded_property_share",
                "open_property_share",
                "constraint_density",
                "cross_module_reference_share",
                "shared_vocabulary_overlap_ratio",
            },
        )

    def test_compare_reports_partial_alignment_gaps(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            left = assess(str(FIXTURES / "profiles" / "synthetic_solution_a.yaml"))
            right = assess(str(FIXTURES / "profiles" / "synthetic_solution_b.yaml"))
            left_path = Path(tmpdir) / "left.json"
            right_path = Path(tmpdir) / "right.json"
            left_path.write_text(json.dumps(left), encoding="utf-8")
            right_path.write_text(json.dumps(right), encoding="utf-8")
            result = compare(
                str(left_path),
                str(right_path),
                str(FIXTURES / "alignments" / "synthetic_solution_partial_alignment.yaml"),
            )

        alignment = result["content"]["alignment"]["alignment_aware_comparison"]
        self.assertEqual(alignment["matched_pair_count"], 1)
        self.assertEqual(alignment["left_present_count"], 2)
        self.assertEqual(alignment["right_present_count"], 2)
        gap_statuses = [item["pair_status"] for item in alignment["ranked_alignment_observations"]]
        self.assertEqual(gap_statuses, ["left_only", "right_only"])
        self.assertIn("only the left-side entity is present", alignment["ranked_alignment_observations"][0]["message"])

    def test_prioritize_includes_alignment_gap_targets(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            assessment = assess(str(FIXTURES / "profiles" / "synthetic_solution_a.yaml"))
            left = assess(str(FIXTURES / "profiles" / "synthetic_solution_a.yaml"))
            right = assess(str(FIXTURES / "profiles" / "synthetic_solution_b.yaml"))
            assessment_path = Path(tmpdir) / "assessment.json"
            left_path = Path(tmpdir) / "left.json"
            right_path = Path(tmpdir) / "right.json"
            comparison_path = Path(tmpdir) / "comparison.json"
            assessment_path.write_text(json.dumps(assessment), encoding="utf-8")
            left_path.write_text(json.dumps(left), encoding="utf-8")
            right_path.write_text(json.dumps(right), encoding="utf-8")
            comparison_result = compare(
                str(left_path),
                str(right_path),
                str(FIXTURES / "alignments" / "synthetic_solution_partial_alignment.yaml"),
            )
            comparison_path.write_text(json.dumps(comparison_result), encoding="utf-8")
            prioritization = prioritize(str(assessment_path), comparison_path=str(comparison_path))

        alignment_targets = [
            item for item in prioritization["content"]["targets"]
            if item["rule_trace"]["rule"] == "alignment_gap"
        ]
        self.assertEqual(len(alignment_targets), 2)
        self.assertEqual(alignment_targets[0]["rule_trace"]["pair_status"], "left_only")
        self.assertEqual(alignment_targets[1]["rule_trace"]["pair_status"], "right_only")

    def test_prioritize_aggregates_redundancy_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            assessment = assess(str(FIXTURES / "profiles" / "synthetic_redundancy_profile.yaml"))
            assessment_path = Path(tmpdir) / "assessment.json"
            assessment_path.write_text(json.dumps(assessment), encoding="utf-8")
            prioritization = prioritize(str(assessment_path))

        redundancy_targets = [
            item for item in prioritization["content"]["targets"]
            if item["rule_trace"]["rule"] == "redundancy_candidate"
        ]
        self.assertEqual(len(redundancy_targets), 1)
        self.assertIn("redundancy candidates were detected", redundancy_targets[0]["message"])

    def test_prioritize_filters_to_directional_comparison_improvement_targets(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            left = assess(str(FIXTURES / "profiles" / "synthetic_solution_a.yaml"))
            right = assess(str(FIXTURES / "profiles" / "synthetic_solution_b.yaml"))
            assessment_path = Path(tmpdir) / "assessment.json"
            left_path = Path(tmpdir) / "left.json"
            right_path = Path(tmpdir) / "right.json"
            comparison_path = Path(tmpdir) / "comparison.json"
            assessment_path.write_text(json.dumps(left), encoding="utf-8")
            left_path.write_text(json.dumps(left), encoding="utf-8")
            right_path.write_text(json.dumps(right), encoding="utf-8")
            comparison_result = compare(str(left_path), str(right_path))
            comparison_path.write_text(json.dumps(comparison_result), encoding="utf-8")
            prioritization = prioritize(str(assessment_path), comparison_path=str(comparison_path))

        comparison_targets = [
            item for item in prioritization["content"]["targets"]
            if item["rule_trace"]["rule"] == "comparison_delta"
        ]
        metric_target_ids = {item["target_id"] for item in comparison_targets}
        self.assertIn("comparison_metric_delta_1", metric_target_ids)
        self.assertNotIn("comparison_metric_delta_5", metric_target_ids)

    def test_summarize_emits_compact_interpretation(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            coverage_result = coverage(
                str(FIXTURES / "profiles" / "synthetic_evolution_latest.yaml"),
                str(FIXTURES / "use_cases" / "product_identity_lookup.yaml"),
            )
            coverage_path = Path(tmpdir) / "coverage.json"
            coverage_path.write_text(json.dumps(coverage_result), encoding="utf-8")
            summary = summarize([str(coverage_path)])

        self.assertEqual(summary["result_type"], "summary_result")
        self.assertEqual(summary["inputs"]["result_count"], 1)
        self.assertIn("headline", summary["content"])
        self.assertGreaterEqual(len(summary["content"]["key_points"]), 1)
        markdown = render_markdown(summary)
        self.assertIn("# Summary", markdown)
        self.assertIn("## Key Points", markdown)

    def test_discovery_artifacts_are_loadable(self) -> None:
        self.assertEqual(schema("profile")["content"]["artifact_kind"], "schema")
        self.assertEqual(schema("assessment_result")["content"]["artifact_kind"], "schema")
        self.assertEqual(template("profile")["content"]["artifact_kind"], "template")
        self.assertEqual(vocabulary("join_kinds")["content"]["artifact_kind"], "vocabulary")

    def test_public_api_functions_have_docstrings(self) -> None:
        import dpawb.api as api

        for name in api.__all__:
            self.assertIsNotNone(getattr(api, name).__doc__, msg=f"{name} is missing a docstring")

    def test_example_input_files_validate_against_schemas(self) -> None:
        schema_by_kind = {
            "profiles": Draft202012Validator(schema("profile")["content"]["document"]),
            "use_cases": Draft202012Validator(schema("use_case")["content"]["document"]),
            "alignments": Draft202012Validator(schema("alignment")["content"]["document"]),
        }
        for directory_name, validator in schema_by_kind.items():
            paths = sorted(EXAMPLES.glob(f"**/{directory_name}/*.yaml"))
            self.assertGreater(len(paths), 0, msg=f"no example {directory_name} files found")
            for path in paths:
                document = yaml.safe_load(path.read_text(encoding="utf-8"))
                errors = list(validator.iter_errors(document))
                self.assertEqual(errors, [], msg=f"{path} schema errors: {[error.message for error in errors]}")

    def test_example_local_shacl_proxies_are_parseable(self) -> None:
        ttl_paths = sorted(EXAMPLES.glob("**/models/*.ttl"))
        self.assertGreater(len(ttl_paths), 0)
        for path in ttl_paths:
            graph = rdflib.Graph()
            graph.parse(path, format="turtle")
            self.assertGreater(len(graph), 0, msg=f"{path} parsed as an empty graph")

    def test_example_summary_results_validate_against_schema(self) -> None:
        validator = Draft202012Validator(schema("summary_result")["content"]["document"])
        summary_paths = sorted(EXAMPLES.glob("**/results/summary.json"))
        self.assertGreater(len(summary_paths), 0)
        for path in summary_paths:
            document = json.loads(path.read_text(encoding="utf-8"))
            errors = list(validator.iter_errors(document))
            self.assertEqual(errors, [], msg=f"{path} schema errors: {[error.message for error in errors]}")

    def test_results_validate_against_built_in_output_schemas(self) -> None:
        assessment_result = assess(str(FIXTURES / "profiles" / "synthetic_solution_a.yaml"))
        coverage_result = coverage(
            str(FIXTURES / "profiles" / "synthetic_evolution_latest.yaml"),
            str(FIXTURES / "use_cases" / "product_identity_lookup.yaml"),
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            left = Path(tmpdir) / "left.json"
            right = Path(tmpdir) / "right.json"
            left.write_text(json.dumps(assessment_result), encoding="utf-8")
            right.write_text(json.dumps(assessment_result), encoding="utf-8")
            comparison_result = compare(str(left), str(right))
            coverage_path = Path(tmpdir) / "coverage.json"
            coverage_path.write_text(json.dumps(coverage_result), encoding="utf-8")
            prioritization_result = prioritize(str(left), coverage_paths=[str(coverage_path)])
            summary_result = summarize([str(coverage_path)])

        schema_names = {
            "assessment_result": assessment_result,
            "coverage_result": coverage_result,
            "comparison_result": comparison_result,
            "prioritization_result": prioritization_result,
            "summary_result": summary_result,
        }
        for schema_name, document in schema_names.items():
            schema_document = schema(schema_name)["content"]["document"]
            validator = Draft202012Validator(schema_document)
            errors = list(validator.iter_errors(document))
            self.assertEqual(errors, [], msg=f"{schema_name} schema errors: {[error.message for error in errors]}")


if __name__ == "__main__":
    unittest.main()
