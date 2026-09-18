from __future__ import annotations

from typing import Any

from .exceptions import ValidationError
from .pir import PIR


class TextPIR(PIR):
    type_name = "text"

    def __init__(self, record_id: int | None = None, text: str = "") -> None:
        super().__init__(record_id)
        if not isinstance(text, str) or not text.strip():
            raise ValidationError("Text content cannot be blank")
        self.text = text
        self._freeze()

    def get_text(self) -> str:
        return self.text

    def get_fields(self) -> dict[str, Any]:
        return {"text": self.text}

    def __str__(self) -> str:
        return f"#{self.get_id()} [text] {self.text}"
