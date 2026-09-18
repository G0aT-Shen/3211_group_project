"""Base model classes and common date helpers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
import re
from typing import Any

from .exceptions import ValidationError

DATETIME_FORMAT = "%Y-%m-%d %H:%M"


def parse_datetime(value: Any) -> datetime:
    """Parse a CLI value or ISO value into a naive datetime."""
    if isinstance(value, datetime):
        if value.tzinfo is not None or value.second or value.microsecond:
            raise ValidationError("Time must be local, timezone-naive and precise to the minute")
        return value
    if not isinstance(value, str) or not value.strip():
        raise ValidationError("Time must be YYYY-MM-DD HH:MM")
    text = value.strip()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}(?:[ T]\d{2}:\d{2}(?::00)?)?", text):
        raise ValidationError("Time must use YYYY-MM-DD HH:MM (or a date alone)")
    for fmt in (DATETIME_FORMAT, "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    raise ValidationError(f"Invalid time: {value} (expected YYYY-MM-DD HH:MM)")


def format_datetime(value: datetime) -> str:
    return value.strftime(DATETIME_FORMAT)


class PIR(ABC):
    """Abstract personal information record."""

    type_name = "pir"

    def __setattr__(self, name: str, value: Any) -> None:
        if getattr(self, "_sealed", False):
            raise AttributeError("PIR records are immutable; use PIMManager.edit_pir")
        object.__setattr__(self, name, value)

    def _freeze(self) -> None:
        self._sealed = True

    def __delattr__(self, name: str) -> None:
        raise AttributeError("PIR fields cannot be deleted; use PIMManager.edit_pir")

    def __init__(self, record_id: int | None = None) -> None:
        if record_id is not None and (not isinstance(record_id, int) or isinstance(record_id, bool) or record_id < 1):
            raise ValidationError("ID must be a positive integer")
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

    @staticmethod
    def from_dict(data: dict[str, Any]) -> PIR:
        """Restore a validated record using the model factory."""
        from .factory import PIRFactory
        return PIRFactory.from_dict(data)

    @abstractmethod
    def __str__(self) -> str:
        pass
