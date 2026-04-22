from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from dpawb.api import assess, capabilities, compare, coverage, prioritize, schema, template, vocabulary


FIXTURES = Path("fixtures")


class PipelineTests(unittest.TestCase):
    def test_capabilities_enumerates_contract_surface(self) -> None:
        result = capabilities()
        self.assertEqual(result["result_type"], "capabilities_result")
        self.assertIn("assess", [item["command"] for item in result["commands"]])
        self.assertIn("alignment", result["schemas"])

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

    def test_discovery_artifacts_are_loadable(self) -> None:
        self.assertEqual(schema("profile")["artifact_kind"], "schema")
        self.assertEqual(schema("assessment_result")["artifact_kind"], "schema")
        self.assertEqual(template("profile")["artifact_kind"], "template")
        self.assertEqual(vocabulary("join_kinds")["artifact_kind"], "vocabulary")

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

        schema_names = {
            "assessment_result": assessment_result,
            "coverage_result": coverage_result,
            "comparison_result": comparison_result,
            "prioritization_result": prioritization_result,
        }
        for schema_name, document in schema_names.items():
            schema_document = schema(schema_name)["content"]
            validator = Draft202012Validator(schema_document)
            errors = list(validator.iter_errors(document))
            self.assertEqual(errors, [], msg=f"{schema_name} schema errors: {[error.message for error in errors]}")


if __name__ == "__main__":
    unittest.main()
