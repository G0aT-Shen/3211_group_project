"""Strict UTF-8 JSON persistence with atomic replacement."""
from __future__ import annotations
import json
import os
from pathlib import Path
import stat
import tempfile
from model import PIMManager
from model.exceptions import StorageError, ValidationError

MAX_FILE_BYTES = 10 * 1024 * 1024


def _read_opener(path, flags):
    # Opening a FIFO must not wait for a writer. Reject symlink replacements
    # between path validation and open on platforms providing O_NOFOLLOW.
    return os.open(path, flags | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_NOFOLLOW", 0))


def pim_path(path: str | Path) -> Path:
    if not isinstance(path, (str, Path)) or not str(path).strip() or "\x00" in str(path):
        raise StorageError("Invalid file path")
    target = Path(path)
    if target.suffix.lower() != ".pim":
        raise StorageError("File extension must be .pim")
    try:
        if target.is_symlink():
            raise StorageError("Symlinks cannot be used as .pim files")
    except OSError as exc:
        raise StorageError(f"Could not inspect file path {target}: {exc}") from exc
    return target


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValidationError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def reject_constant(value):
    raise ValidationError(f"JSON constant is not allowed: {value}")


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
                raise StorageError("File exceeds the 10 MiB limit")
            with tempfile.NamedTemporaryFile(mode="wb", dir=target.parent, prefix=".pim-", suffix=".tmp", delete=False) as stream:
                temporary = Path(stream.name)
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, target)
            temporary = None
        except (OSError, ValueError, UnicodeError, ValidationError) as exc:
            raise StorageError(f"Could not save {target}: {exc}") from exc
        finally:
            if temporary is not None:
                try:
                    temporary.unlink(missing_ok=True)
                except OSError as exc:
                    raise StorageError(f"Save incomplete and temporary file {temporary} could not be removed: {exc}") from exc

    @staticmethod
    def load(path: str | Path) -> PIMManager:
        target = pim_path(path)
        try:
            with open(target, "rb", opener=_read_opener) as stream:
                if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                    raise StorageError("A .pim input must be a regular file")
                payload = stream.read(MAX_FILE_BYTES + 1)
            if len(payload) > MAX_FILE_BYTES:
                raise StorageError("File exceeds the 10 MiB limit")
            data = json.loads(payload.decode("utf-8"), object_pairs_hook=unique_object, parse_constant=reject_constant)
            return PIMManager.from_dict(data)
        except (OSError, UnicodeError, ValueError, ValidationError, RecursionError) as exc:
            raise StorageError(f"Could not read .pim file {target}: {exc}") from exc
