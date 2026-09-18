"""One field schema shared by record creation, editing and the CLI."""
from __future__ import annotations
from typing import Any
from .contact_pir import ContactPIR
from .event_pir import EventPIR
from .exceptions import ValidationError
from .pir import PIR
from .task_pir import TaskPIR
from .text_pir import TextPIR

FIELD_SCHEMAS = {
    "text": ("text",),
    "task": ("description", "deadline"),
    "event": ("description", "start_time", "alarm"),
    "contact": ("name", "address", "mobile"),
}
RECORD_CLASSES = {"text": TextPIR, "task": TaskPIR, "event": EventPIR, "contact": ContactPIR}


class PIRFactory:
    @staticmethod
    def normalize_fields(type_name: str, fields: dict[str, Any], partial: bool = False) -> dict[str, Any]:
        """Validate field names and required fields before touching a record."""
        if not isinstance(type_name, str) or type_name.lower() not in FIELD_SCHEMAS:
            raise ValidationError(f"不支持的 PIR 类型：{type_name}")
        if not isinstance(fields, dict) or not all(isinstance(key, str) for key in fields):
            raise ValidationError("字段必须是字符串键的字典")
        result = dict(fields)
        if "start" in result:
            if "start_time" in result:
                raise ValidationError("start 与 start_time 不能重复指定")
            result["start_time"] = result.pop("start")
        allowed = set(FIELD_SCHEMAS[type_name.lower()])
        unknown = result.keys() - allowed
        if unknown:
            raise ValidationError(f"不适用于 {type_name} 的字段：{', '.join(sorted(unknown))}")
        if not partial and allowed - result.keys():
            raise ValidationError(f"缺少字段：{', '.join(sorted(allowed - result.keys()))}")
        if partial and not result:
            raise ValidationError("至少需要修改一个字段")
        return result

    @staticmethod
    def create(type_name: str, fields: dict[str, Any], record_id: int | None = None) -> PIR:
        values = PIRFactory.normalize_fields(type_name, fields)
        return RECORD_CLASSES[type_name.lower()](record_id=record_id, **values)

    @staticmethod
    def from_dict(data: dict[str, Any]) -> PIR:
        if not isinstance(data, dict) or not {"id", "type"} <= data.keys():
            raise ValidationError("PIR 数据必须包含 id 和 type")
        if type(data["id"]) is not int or data["id"] < 1:
            raise ValidationError("已保存 PIR 的 ID 必须是正整数")
        return PIRFactory.create(data["type"], {key: value for key, value in data.items() if key not in {"id", "type"}}, data["id"])
