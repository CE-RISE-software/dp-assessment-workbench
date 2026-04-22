from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class DpawbError(Exception):
    message: str
    code: str
    details: list[dict[str, object]] = field(default_factory=list)
    exit_code: int = 1

    def to_result(self) -> dict[str, object]:
        return {
            "result_type": "error_result",
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
            },
        }


class InputError(DpawbError):
    def __init__(self, message: str, details: list[dict[str, object]] | None = None) -> None:
        super().__init__(
            message=message,
            code="input_error",
            details=details or [],
            exit_code=2,
        )


class ProcessingError(DpawbError):
    def __init__(self, message: str, details: list[dict[str, object]] | None = None) -> None:
        super().__init__(
            message=message,
            code="processing_error",
            details=details or [],
            exit_code=3,
        )
