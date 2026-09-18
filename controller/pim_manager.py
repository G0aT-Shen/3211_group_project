"""In-memory PIM aggregate and model factory."""

from __future__ import annotations

from typing import Any, Iterable

from model import ContactPIR, EventPIR, PIR, TaskPIR, TextPIR, parse_datetime
from model.exceptions import PIRNotFoundError, ValidationError


class PIRFactory:
    """Create model instances from CLI fields or persisted dictionaries."""

    @staticmethod
    def create(type_name: str, fields: dict[str, Any], record_id: int | None = None) -> PIR:
        normalized = type_name.lower()
        if normalized == "text":
            return TextPIR(record_id, fields.get("text", fields.get("description", "")))
        if normalized == "task":
            return TaskPIR(record_id, fields.get("description", ""), fields.get("deadline"))
        if normalized == "event":
            return EventPIR(record_id, fields.get("description", ""), fields.get("start_time", fields.get("start")), fields.get("alarm"))
        if normalized == "contact":
            return ContactPIR(record_id, fields.get("name", ""), fields.get("address", ""), fields.get("mobile", ""))
        raise ValidationError(f"不支持的 PIR 类型：{type_name}")

    @staticmethod
    def from_dict(data: dict[str, Any]) -> PIR:
        if not isinstance(data, dict) or "type" not in data:
            raise ValidationError("PIR 数据缺少 type")
        record_id = data.get("id")
        return PIRFactory.create(data["type"], data, record_id)


class PIMManager:
    """Manage records, IDs, CRUD operations, search, and serialization."""

    def __init__(self, pirs: Iterable[PIR] | None = None, next_id: int = 1) -> None:
        self.pirs: dict[int, PIR] = {}
        for pir in pirs or []:
            self._insert_existing(pir)
        self.next_id = max(next_id, max(self.pirs, default=0) + 1)

    def _insert_existing(self, pir: PIR) -> None:
        if pir.get_id() is None:
            raise ValidationError("已持久化 PIR 必须有 ID")
        if pir.get_id() in self.pirs:
            raise ValidationError(f"重复的 PIR ID：{pir.get_id()}")
        self.pirs[pir.get_id()] = pir

    def add_pir(self, pir: PIR) -> PIR:
        if pir.get_id() is not None:
            raise ValidationError("新增 PIR 不应预先指定 ID")
        pir._id = self.next_id
        self.pirs[self.next_id] = pir
        self.next_id += 1
        return pir

    def get_pir(self, record_id: int) -> PIR:
        try:
            return self.pirs[int(record_id)]
        except (KeyError, TypeError, ValueError):
            raise PIRNotFoundError(f"找不到 PIR #{record_id}") from None

    def edit_pir(self, record_id: int, updates: dict[str, Any] | str, value: Any = None) -> PIR:
        pir = self.get_pir(record_id)
        if isinstance(updates, str):
            updates = {updates: value}
        updates = {"start_time" if key == "start" else key: val for key, val in updates.items()}
        fields = pir.get_fields()
        fields.update(updates)
        replacement = PIRFactory.create(pir.get_type(), fields, pir.get_id())
        self.pirs[pir.get_id()] = replacement
        return replacement

    def delete_pir(self, record_id: int) -> bool:
        self.get_pir(record_id)
        del self.pirs[int(record_id)]
        return True

    def list_all(self) -> list[PIR]:
        return [self.pirs[key] for key in sorted(self.pirs)]

    def search(self, node: Any) -> list[PIR]:
        return [pir for pir in self.list_all() if node.evaluate(pir)]

    def to_dict(self) -> dict[str, Any]:
        return {"schema_version": 1, "next_id": self.next_id, "pirs": [pir.to_dict() for pir in self.list_all()]}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PIMManager":
        if not isinstance(data, dict) or not isinstance(data.get("pirs"), list):
            raise ValidationError(".pim 文件必须包含 pirs 数组")
        if data.get("schema_version", 1) != 1:
            raise ValidationError(f"不支持的 schema_version：{data.get('schema_version')}")
        pirs = [PIRFactory.from_dict(item) for item in data["pirs"]]
        next_id = data.get("next_id", max((pir.get_id() or 0 for pir in pirs), default=0) + 1)
        if not isinstance(next_id, int) or next_id < 1:
            next_id = max((pir.get_id() or 0 for pir in pirs), default=0) + 1
        return cls(pirs, next_id)
