from __future__ import annotations


def build_result(
    result_type: str,
    inputs: dict[str, object],
    content: dict[str, object],
    diagnostics: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    return {
        "result_type": result_type,
        "inputs": inputs,
        "content": content,
        "diagnostics": diagnostics or [],
    }
