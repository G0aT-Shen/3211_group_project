"""Parse CLI syntax without executing commands or modifying state."""
from __future__ import annotations
from dataclasses import dataclass, field
import re
import shlex
from model.exceptions import InvalidCommandError, ValidationError
from model.factory import FIELD_SCHEMAS, PIRFactory


@dataclass
class Command:
    name: str
    args: list[str] = field(default_factory=list)
    options: dict[str, str] = field(default_factory=dict)


def positive_id(value: str) -> str:
    if not re.fullmatch(r"[0-9]{1,100}", value) or int(value) < 1:
        raise InvalidCommandError("ID 必须是正整数（最多 100 位）")
    return value


class CommandParser:
    def parse(self, line: str) -> Command:
        if not isinstance(line, str) or not line.strip():
            raise InvalidCommandError("命令不能为空")
        if len(line) > 16384:
            raise InvalidCommandError("命令过长（最多 16384 字符）")
        parts = line.strip().split(maxsplit=1)
        name = parts[0].lower()
        tail = parts[1] if len(parts) == 2 else ""
        if name == "search":
            if not tail.strip():
                raise InvalidCommandError("用法：search <expression>")
            # Keep literal quotes; remove an optional single pair around the whole expression.
            try:
                tokens = shlex.split(tail)
            except ValueError as exc:
                raise InvalidCommandError(f"命令引号不匹配：{exc}") from exc
            if len(tokens) == 1 and tail[0] in "\"'":
                tail = tokens[0]
            return Command(name, [tail])
        try:
            args = shlex.split(tail)
        except ValueError as exc:
            raise InvalidCommandError(f"命令引号不匹配：{exc}") from exc
        if name == "quit":
            name = "exit"
        if name in {"help", "exit"}:
            if args:
                raise InvalidCommandError(f"{name} 不接受参数")
            return Command(name)
        if name in {"print", "delete", "save", "load"}:
            if len(args) > 1 or (name in {"delete", "load"} and not args):
                raise InvalidCommandError(f"用法：{name} <参数>")
            if name in {"delete", "print"} and args and not (name == "print" and args[0].lower() == "all"):
                positive_id(args[0])
            if args and not args[0]:
                raise InvalidCommandError("参数不能为空")
            return Command(name, args)
        if name == "add":
            if not args or args[0].lower() not in FIELD_SCHEMAS:
                raise InvalidCommandError("用法：add text|task|event|contact ...")
            type_name = args.pop(0).lower()
            options = {}
            if type_name != "contact":
                if not args or args[0].startswith("--"):
                    raise InvalidCommandError(f"add {type_name} 需要带引号的文本或描述")
                options["text" if type_name == "text" else "description"] = args.pop(0)
            parsed = self._options(args)
            if options.keys() & parsed.keys():
                raise InvalidCommandError("文本或描述不能重复指定")
            options.update(parsed)
            try:
                options = PIRFactory.normalize_fields(type_name, options)
            except ValidationError as exc:
                raise InvalidCommandError(str(exc)) from exc
            return Command(name, [type_name], options)
        if name == "edit":
            if not args:
                raise InvalidCommandError("用法：edit <id> --field value")
            record_id = positive_id(args.pop(0))
            options = self._options(args)
            if not options:
                raise InvalidCommandError("edit 至少需要一个 --field value")
            return Command(name, [record_id], options)
        raise InvalidCommandError(f"未知命令：{name}")

    def _options(self, tokens: list[str]) -> dict[str, str]:
        options = {}
        index = 0
        allowed = set().union(*map(set, FIELD_SCHEMAS.values()))
        while index < len(tokens):
            token = tokens[index]
            if not token.startswith("--"):
                raise InvalidCommandError(f"多余参数：{token}；含空格的文本须加引号")
            key = token[2:].lower().replace("-", "_")
            key = "start_time" if key == "start" else key
            if key not in allowed:
                raise InvalidCommandError(f"未知字段：{key}")
            if key in options:
                raise InvalidCommandError(f"重复字段：{key}")
            if index + 1 >= len(tokens) or tokens[index + 1].startswith("--"):
                raise InvalidCommandError(f"字段 {key} 缺少值")
            value = tokens[index + 1]
            index += 2
            if key in {"deadline", "start_time", "alarm"} and re.fullmatch(r"\d{4}-\d{2}-\d{2}", value) and index < len(tokens) and re.fullmatch(r"\d{2}:\d{2}", tokens[index]):
                value += " " + tokens[index]
                index += 1
            options[key] = value
        return options
