from __future__ import annotations

from datetime import datetime
from typing import Any

from .exceptions import ValidationError
from .pir import PIR, format_datetime, parse_datetime


class TaskPIR(PIR):
    type_name = "task"

    def __init__(self, record_id: int | None = None, description: str = "", deadline: datetime | str | None = None) -> None:
        super().__init__(record_id)
        if not isinstance(description, str) or not description.strip():
            raise ValidationError("任务描述不能为空")
        if deadline is None:
            raise ValidationError("任务必须提供 deadline")
        self.description = description
        self.deadline = parse_datetime(deadline)

    def get_deadline(self) -> datetime:
        return self.deadline

    def get_fields(self) -> dict[str, Any]:
        return {"description": self.description, "deadline": self.deadline.isoformat()}

    def __str__(self) -> str:
        return f"#{self.get_id()} [task] {self.description} (deadline: {format_datetime(self.deadline)})"
