from __future__ import annotations

from datetime import datetime
from typing import Any

from .exceptions import ValidationError
from .pir import PIR, _validate_required_text, format_datetime, parse_datetime


class TaskPIR(PIR):
    type_name = "task"

    def __init__(self, record_id: int | None = None, description: str = "", deadline: datetime | str | None = None) -> None:
        super().__init__(record_id)
        description = _validate_required_text(description, "Task description")
        if deadline is None:
            raise ValidationError("Task requires a deadline")
        self.description = description
        self.deadline = parse_datetime(deadline)
        self._freeze()

    def get_description(self) -> str:
        return self.description

    def get_deadline(self) -> datetime:
        return self.deadline

    def get_fields(self) -> dict[str, Any]:
        return {"description": self.description, "deadline": self.deadline.isoformat()}

    def __str__(self) -> str:
        return f"#{self.get_id()} [task] {self.description} (deadline: {format_datetime(self.deadline)})"
