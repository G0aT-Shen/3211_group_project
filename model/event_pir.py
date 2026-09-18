from __future__ import annotations

from datetime import datetime
from typing import Any

from .exceptions import ValidationError
from .pir import PIR, format_datetime, parse_datetime


class EventPIR(PIR):
    type_name = "event"

    def __init__(self, record_id: int | None = None, description: str = "", start_time: datetime | str | None = None, alarm: datetime | str | None = None) -> None:
        super().__init__(record_id)
        if not isinstance(description, str) or not description.strip():
            raise ValidationError("事件描述不能为空")
        if start_time is None or alarm is None:
            raise ValidationError("事件必须提供 start 和 alarm")
        self.description = description
        self.start_time = parse_datetime(start_time)
        self.alarm = parse_datetime(alarm)
        self._freeze()

    def get_description(self) -> str:
        return self.description

    def get_start_time(self) -> datetime:
        return self.start_time

    def get_alarm(self) -> datetime:
        return self.alarm

    def get_fields(self) -> dict[str, Any]:
        return {"description": self.description, "start_time": self.start_time.isoformat(), "alarm": self.alarm.isoformat()}

    def __str__(self) -> str:
        return f"#{self.get_id()} [event] {self.description} (start: {format_datetime(self.start_time)}, alarm: {format_datetime(self.alarm)})"
