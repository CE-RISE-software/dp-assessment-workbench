from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from dpawb.errors import InputError


def load_yaml_file(path: str | Path) -> dict[str, Any]:
    source_path = Path(path)
    try:
        with source_path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
    except FileNotFoundError as exc:
        raise InputError(f"YAML input does not exist: {source_path}") from exc
    except yaml.YAMLError as exc:
        raise InputError(
            f"YAML input is invalid: {source_path}",
            details=[{"path": str(source_path), "error": str(exc)}],
        ) from exc
    if not isinstance(data, dict):
        raise InputError(
            f"YAML input must be a mapping at top level: {source_path}",
            details=[{"path": str(source_path)}],
        )
    return data


def load_json_file(path: str | Path) -> dict[str, Any]:
    source_path = Path(path)
    try:
        with source_path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except FileNotFoundError as exc:
        raise InputError(f"JSON input does not exist: {source_path}") from exc
    except json.JSONDecodeError as exc:
        raise InputError(
            f"JSON input is invalid: {source_path}",
            details=[{"path": str(source_path), "error": str(exc)}],
        ) from exc
    if not isinstance(data, dict):
        raise InputError(
            f"JSON input must be an object at top level: {source_path}",
            details=[{"path": str(source_path)}],
        )
    return data


def dump_json(data: dict[str, Any]) -> str:
    return json.dumps(data, indent=2, sort_keys=True) + "\n"
