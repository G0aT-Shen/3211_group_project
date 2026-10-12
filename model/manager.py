"""Pure, IO-free application model: record collection and ID invariants."""
from __future__ import annotations
from typing import Any, Iterable, Protocol
from types import MappingProxyType
from .pir import PIR
from .factory import PIRFactory
from .exceptions import PIRNotFoundError, ValidationError
from .ids import MAX_RECORD_ID, validate_next_id, validate_record_id


class Criterion(Protocol):
    def evaluate(self, pir: PIR) -> bool:
        ...


class PIMManager:
    def __init__(self, pirs: Iterable[PIR] | None = None, next_id: int = 1) -> None:
        self._pirs: dict[int, PIR] = {}
        validate_next_id(next_id)
        for pir in pirs or ():
            if not isinstance(pir, PIR) or pir.get_id() is None:
                raise ValidationError("Existing records must be PIRs with IDs")
            record_id = pir.get_id()
            validate_record_id(record_id)
            if record_id in self._pirs:
                raise ValidationError(f"Duplicate PIR ID: {record_id}")
            self._pirs[record_id] = pir
        self._next_id = max(next_id, max(self._pirs, default=0) + 1)

    @property
    def pirs(self):
        return MappingProxyType(self._pirs)

    @property
    def next_id(self) -> int:
        return self._next_id

    def add_pir(self, pir: PIR) -> PIR:
        if not isinstance(pir, PIR) or pir.get_id() is not None:
            raise ValidationError("A new record must be a PIR without an assigned ID")
        if self._next_id > MAX_RECORD_ID:
            raise ValidationError("ID space is exhausted; no further records can be added to this collection")
        record_id = self._next_id
        assigned = PIRFactory.create(pir.get_type(), pir.get_fields(), record_id)
        try:
            self._pirs[record_id] = assigned
            self._next_id = record_id + 1
        except KeyboardInterrupt:
            # Keep the record/counter pair consistent when the REPL resumes.
            self._pirs.pop(record_id, None)
            self._next_id = record_id
            raise
        return assigned

    def get_pir(self, record_id: int) -> PIR:
        validate_record_id(record_id)
        if record_id not in self._pirs:
            raise PIRNotFoundError(f"PIR #{record_id} was not found")
        return self._pirs[record_id]

    def edit_pir(self, record_id: int, updates: dict[str, Any] | str, value: Any = None) -> PIR:
        pir = self.get_pir(record_id)
        if isinstance(updates, str):
            updates = {updates: value}
        updates = PIRFactory.normalize_fields(pir.get_type(), updates, partial=True)
        replacement = PIRFactory.create(pir.get_type(), {**pir.get_fields(), **updates}, record_id)
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
            raise ValidationError("The .pim root must contain exactly schema_version, next_id and pirs")
        if type(data["schema_version"]) is not int or data["schema_version"] != 1:
            raise ValidationError("Unsupported schema_version (current version is 1)")
        if not isinstance(data["pirs"], list):
            raise ValidationError("pirs must be an array")
        pirs = [PIRFactory.from_dict(item) for item in data["pirs"]]
        next_id = data["next_id"]
        validate_next_id(next_id)
        if next_id <= max((pir.get_id() for pir in pirs), default=0):
            raise ValidationError("next_id must be a positive integer greater than every existing ID")
        return cls(pirs, next_id)
