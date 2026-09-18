"""Base model classes and common date helpers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from .exceptions import ValidationError

DATETIME_FORMAT = "%Y-%m-%d %H:%M"


def parse_datetime(value: Any) -> datetime:
    """Parse a CLI value or ISO value into a naive datetime."""
    if isinstance(value, datetime):
        return value
    if not isinstance(value, str) or not value.strip():
        raise ValidationError("时间必须是 YYYY-MM-DD HH:MM")
    text = value.strip()
    for fmt in (DATETIME_FORMAT, "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    raise ValidationError(f"无效时间：{value}（格式应为 YYYY-MM-DD HH:MM）")


def format_datetime(value: datetime) -> str:
    return value.strftime(DATETIME_FORMAT)


class PIR(ABC):
    """Abstract personal information record."""

    type_name = "pir"

    def __init__(self, record_id: int | None = None) -> None:
        if record_id is not None and (not isinstance(record_id, int) or isinstance(record_id, bool) or record_id < 1):
            raise ValidationError("ID 必须是正整数")
        self._id = record_id

    def get_id(self) -> int | None:
        return self._id

    def get_type(self) -> str:
        return self.type_name

    @abstractmethod
    def get_fields(self) -> dict[str, Any]:
        """Return fields excluding id and type."""

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {"id": self._id, "type": self.type_name}
        data.update(self.get_fields())
        return data

    @abstractmethod
    def __str__(self) -> str:
        pass
