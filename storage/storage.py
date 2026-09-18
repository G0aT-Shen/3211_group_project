"""Strict UTF-8 JSON persistence with atomic replacement."""
from __future__ import annotations
import json
import os
from pathlib import Path
import tempfile
from model import PIMManager
from model.exceptions import StorageError, ValidationError

MAX_FILE_BYTES = 10 * 1024 * 1024


def pim_path(path: str | Path) -> Path:
    if not isinstance(path, (str, Path)) or not str(path).strip() or "\x00" in str(path):
        raise StorageError("文件路径无效")
    target = Path(path)
    if target.suffix.lower() != ".pim":
        raise StorageError("文件扩展名必须为 .pim")
    try:
        if target.is_symlink():
            raise StorageError("不支持以符号链接作为 .pim 文件")
    except OSError as exc:
        raise StorageError(f"无法检查文件路径 {target}: {exc}") from exc
    return target


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValidationError(f"JSON 重复键：{key}")
        result[key] = value
    return result


def reject_constant(value):
    raise ValidationError(f"JSON 不允许常量：{value}")


class Storage:
    @staticmethod
    def save(path: str | Path, manager: PIMManager) -> None:
        target = pim_path(path)
        temporary = None
        try:
            # Validate the snapshot before creating any file.
            data = manager.to_dict()
            PIMManager.from_dict(data)
            payload = (json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")
            if len(payload) > MAX_FILE_BYTES:
                raise StorageError("文件超过 10 MiB 限制")
            with tempfile.NamedTemporaryFile(mode="wb", dir=target.parent, prefix=".pim-", suffix=".tmp", delete=False) as stream:
                temporary = Path(stream.name)
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, target)
            temporary = None
        except (OSError, ValueError, UnicodeError, ValidationError) as exc:
            raise StorageError(f"无法保存 {target}: {exc}") from exc
        finally:
            if temporary is not None:
                try:
                    temporary.unlink(missing_ok=True)
                except OSError as exc:
                    raise StorageError(f"保存未完成，且无法清理临时文件 {temporary}: {exc}") from exc

    @staticmethod
    def load(path: str | Path) -> PIMManager:
        target = pim_path(path)
        try:
            with target.open("rb") as stream:
                payload = stream.read(MAX_FILE_BYTES + 1)
            if len(payload) > MAX_FILE_BYTES:
                raise StorageError("文件超过 10 MiB 限制")
            data = json.loads(payload.decode("utf-8"), object_pairs_hook=unique_object, parse_constant=reject_constant)
            return PIMManager.from_dict(data)
        except (OSError, UnicodeError, ValueError, ValidationError, RecursionError) as exc:
            raise StorageError(f"无法读取 .pim 文件 {target}: {exc}") from exc
