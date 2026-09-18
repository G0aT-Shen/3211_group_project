"""JSON persistence for .pim files."""

from __future__ import annotations

import json
from pathlib import Path

from controller import PIMManager
from model.exceptions import StorageError


class Storage:
    @staticmethod
    def save(path: str | Path, manager: PIMManager) -> None:
        target = Path(path)
        try:
            target.write_text(json.dumps(manager.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        except OSError as exc:
            raise StorageError(f"无法保存文件 {target}: {exc}") from exc

    @staticmethod
    def load(path: str | Path) -> PIMManager:
        target = Path(path)
        try:
            data = json.loads(target.read_text(encoding="utf-8"))
            return PIMManager.from_dict(data)
        except FileNotFoundError as exc:
            raise StorageError(f"文件不存在：{target}") from exc
        except (OSError, UnicodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
            raise StorageError(f"无法读取 .pim 文件 {target}: {exc}") from exc
