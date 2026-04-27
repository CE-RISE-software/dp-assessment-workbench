from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dpawb.api import (
    assess,
    capabilities,
    compare,
    coverage,
    prioritize,
    recommend_composition,
    schema,
    summarize,
    template,
    vocabulary,
)
from dpawb.errors import DpawbError, InputError
from dpawb.io import dump_json
from dpawb.operations.summarize import render_markdown


def _write_result(result: dict[str, object], output_path: str | None) -> None:
    payload = dump_json(result)
    if output_path:
        Path(output_path).write_text(payload, encoding="utf-8")
    else:
        sys.stdout.write(payload)


def _write_text_result(payload: str, output_path: str | None) -> None:
    if output_path:
        Path(output_path).write_text(payload, encoding="utf-8")
    else:
        sys.stdout.write(payload)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="dpawb")
    subparsers = parser.add_subparsers(dest="command", required=True)

    assess_parser = subparsers.add_parser("assess")
    assess_parser.add_argument("--profile", required=True)
    assess_parser.add_argument("--output")

    coverage_parser = subparsers.add_parser("coverage")
    coverage_parser.add_argument("--profile", required=True)
    coverage_parser.add_argument("--use-case", required=True, dest="use_case")
    coverage_parser.add_argument("--output")

    compare_parser = subparsers.add_parser("compare")
    compare_parser.add_argument("--left", required=True)
    compare_parser.add_argument("--right", required=True)
    compare_parser.add_argument("--alignment")
    compare_parser.add_argument("--output")

    prioritize_parser = subparsers.add_parser("prioritize")
    prioritize_parser.add_argument("--assessment", required=True)
    prioritize_parser.add_argument("--comparison")
    prioritize_parser.add_argument("--coverage", nargs="*", default=[])
    prioritize_parser.add_argument("--output")

    recommend_parser = subparsers.add_parser("recommend-composition")
    recommend_parser.add_argument("--left", required=True)
    recommend_parser.add_argument("--right", required=True)
    recommend_parser.add_argument("--comparison")
    recommend_parser.add_argument("--coverage", nargs="*", default=[])
    recommend_parser.add_argument("--output")

    schema_parser = subparsers.add_parser("schema")
    schema_parser.add_argument(
        "name",
        choices=[
            "profile",
            "use_case",
            "alignment",
            "assessment_result",
            "coverage_result",
            "comparison_result",
            "prioritization_result",
            "composition_recommendation_result",
            "summary_result",
        ],
    )
    schema_parser.add_argument("--output")

    vocabulary_parser = subparsers.add_parser("vocabulary")
    vocabulary_parser.add_argument("name", choices=["item_categories", "join_kinds"])
    vocabulary_parser.add_argument("--output")

    template_parser = subparsers.add_parser("template")
    template_parser.add_argument("name", choices=["profile", "use_case", "alignment"])
    template_parser.add_argument("--output")

    capabilities_parser = subparsers.add_parser("capabilities")
    capabilities_parser.add_argument("--output")

    summarize_parser = subparsers.add_parser("summarize")
    summarize_parser.add_argument("--result", action="append", required=True, dest="results")
    summarize_parser.add_argument("--format", choices=["json", "markdown"], default="json")
    summarize_parser.add_argument("--output")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        match args.command:
            case "assess":
                result = assess(args.profile)
            case "coverage":
                result = coverage(args.profile, args.use_case)
            case "compare":
                result = compare(args.left, args.right, args.alignment)
            case "prioritize":
                result = prioritize(args.assessment, args.comparison, args.coverage)
            case "recommend-composition":
                result = recommend_composition(args.left, args.right, args.comparison, args.coverage)
            case "schema":
                result = schema(args.name)
            case "vocabulary":
                result = vocabulary(args.name)
            case "template":
                result = template(args.name)
            case "capabilities":
                result = capabilities()
            case "summarize":
                result = summarize(args.results)
                if args.format == "markdown":
                    _write_text_result(render_markdown(result), getattr(args, "output", None))
                    return 0
            case _:
                raise InputError(f"Unsupported command: {args.command}")
        _write_result(result, getattr(args, "output", None))
        return 0
    except DpawbError as exc:
        sys.stderr.write(f"{exc.code}: {exc.message}\n")
        _write_result(exc.to_result(), getattr(args, "output", None))
        return exc.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
