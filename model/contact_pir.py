from __future__ import annotations

from typing import Any

from .exceptions import ValidationError
from .pir import PIR


class ContactPIR(PIR):
    type_name = "contact"

    def __init__(self, record_id: int | None = None, name: str = "", address: str = "", mobile: str = "") -> None:
        super().__init__(record_id)
        for label, value in (("姓名", name), ("地址", address), ("手机号", mobile)):
            if not isinstance(value, str) or not value.strip():
                raise ValidationError(f"联系人{label}不能为空")
        self.name, self.address, self.mobile = name, address, mobile

    def get_name(self) -> str:
        return self.name

    def get_address(self) -> str:
        return self.address

    def get_mobile(self) -> str:
        return self.mobile

    def get_fields(self) -> dict[str, Any]:
        return {"name": self.name, "address": self.address, "mobile": self.mobile}

    def __str__(self) -> str:
        return f"#{self.get_id()} [contact] {self.name} (address: {self.address}, mobile: {self.mobile})"
