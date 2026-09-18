"""Pure, IO-free application model: record collection and ID invariants."""
from __future__ import annotations
from typing import Any, Iterable, Protocol
from types import MappingProxyType
from .pir import PIR
from .factory import PIRFactory
from .exceptions import PIRNotFoundError, ValidationError


class Criterion(Protocol):
    def evaluate(self, pir: PIR) -> bool:
        ...


class PIMManager:
    def __init__(self, pirs: Iterable[PIR] | None = None, next_id: int = 1) -> None:
        self._pirs: dict[int, PIR] = {}
        if type(next_id) is not int or next_id < 1:
            raise ValidationError("next_id 必须是正整数")
        for pir in pirs or ():
            if not isinstance(pir, PIR) or pir.get_id() is None:
                raise ValidationError("已有记录必须是带 ID 的 PIR")
            if pir.get_id() in self._pirs:
                raise ValidationError(f"重复的 PIR ID：{pir.get_id()}")
            self._pirs[pir.get_id()] = pir
        self._next_id = max(next_id, max(self._pirs, default=0) + 1)

    @property
    def pirs(self):
        return MappingProxyType(self._pirs)

    @property
    def next_id(self) -> int:
        return self._next_id

    def add_pir(self, pir: PIR) -> PIR:
        if not isinstance(pir, PIR) or pir.get_id() is not None:
            raise ValidationError("新增记录必须是尚未分配 ID 的 PIR")
        assigned = PIRFactory.create(pir.get_type(), pir.get_fields(), self._next_id)
        self._pirs[self._next_id] = assigned
        self._next_id += 1
        return assigned

    def get_pir(self, record_id: int) -> PIR:
        if type(record_id) is not int or record_id < 1:
            raise ValidationError("ID 必须是正整数")
        if record_id not in self._pirs:
            raise PIRNotFoundError(f"找不到 PIR #{record_id}")
        return self._pirs[record_id]

    def edit_pir(self, record_id: int, updates: dict[str, Any] | str, value: Any = None) -> PIR:
        pir = self.get_pir(record_id)
        if isinstance(updates, str):
            updates = {updates: value}
        updates = PIRFactory.normalize_fields(pir.get_type(), updates, partial=True)
        fields = pir.get_fields()
        fields.update(updates)
        replacement = PIRFactory.create(pir.get_type(), fields, record_id)
        self._pirs[record_id] = replacement
        return replacement

    def delete_pir(self, record_id: int) -> bool:
        self.get_pir(record_id)
        del self._pirs[record_id]
        return True

    def list_all(self) -> list[PIR]:
        return [self._pirs[key] for key in sorted(self._pirs)]

    def search(self, node: Criterion) -> list[PIR]:
        return [pir for pir in self.list_all() if node.evaluate(pir)]

    def to_dict(self) -> dict[str, Any]:
        return {"schema_version": 1, "next_id": self._next_id, "pirs": [pir.to_dict() for pir in self.list_all()]}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PIMManager:
        if not isinstance(data, dict) or set(data) != {"schema_version", "next_id", "pirs"}:
            raise ValidationError(".pim 根节点必须包含且仅包含 schema_version、next_id、pirs")
        if type(data["schema_version"]) is not int or data["schema_version"] != 1:
            raise ValidationError("不支持的 schema_version（当前为 1）")
        if not isinstance(data["pirs"], list):
            raise ValidationError("pirs 必须是数组")
        pirs = [PIRFactory.from_dict(item) for item in data["pirs"]]
        next_id = data["next_id"]
        if type(next_id) is not int or next_id <= max((pir.get_id() for pir in pirs), default=0):
            raise ValidationError("next_id 必须是大于所有已有 ID 的正整数")
        return cls(pirs, next_id)
