from __future__ import annotations

import json
from importlib import resources
from typing import Any

import yaml

DATA_PACKAGE = "dpawb.data"


def read_text(relative_path: str) -> str:
    return resources.files(DATA_PACKAGE).joinpath(relative_path).read_text(encoding="utf-8")


def load_json_resource(relative_path: str) -> dict[str, Any]:
    return json.loads(read_text(relative_path))


def load_yaml_resource(relative_path: str) -> Any:
    return yaml.safe_load(read_text(relative_path))
