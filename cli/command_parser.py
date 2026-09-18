"""Shell-like command parsing for the CLI."""

from __future__ import annotations

import shlex
import re
from dataclasses import dataclass, field

from model.exceptions import InvalidCommandError


@dataclass
class Command:
    name: str
    args: list[str] = field(default_factory=list)
    options: dict[str, str] = field(default_factory=dict)


class CommandParser:
    def parse(self, line: str) -> Command:
        try:
            tokens = shlex.split(line)
        except ValueError as exc:
            raise InvalidCommandError(f"命令引号不匹配：{exc}") from exc
        if not tokens:
            raise InvalidCommandError("命令不能为空")
        name = tokens.pop(0).lower()
        if name == "quit":
            name = "exit"
        if name in {"help", "exit"}:
            if tokens:
                raise InvalidCommandError(f"{name} 不接受参数")
            return Command(name)
        if name == "search":
            if not tokens:
                raise InvalidCommandError("用法：search <expression>")
            return Command(name, args=[" ".join(tokens)])
        if name in {"print", "delete", "save", "load"}:
            if len(tokens) > 1:
                raise InvalidCommandError(f"用法：{name} <参数>")
            return Command(name, args=tokens)
        if name == "add":
            return self._parse_add(tokens)
        if name == "edit":
            return self._parse_edit(tokens)
        raise InvalidCommandError(f"未知命令：{name}")

    def _parse_add(self, tokens: list[str]) -> Command:
        if not tokens:
            raise InvalidCommandError("用法：add text|task|event|contact ...")
        type_name = tokens.pop(0).lower()
        if type_name not in {"text", "task", "event", "contact"}:
            raise InvalidCommandError(f"未知 PIR 类型：{type_name}")
        positional: list[str] = []
        options = self._parse_options(tokens)
        raw_positional = options.pop("_positional", [])
        if type_name in {"text", "task", "event"}:
            positional = raw_positional if isinstance(raw_positional, list) else [str(raw_positional)]
        if type_name in {"text", "task", "event"} and not positional:
            raise InvalidCommandError(f"add {type_name} 需要描述或文本内容")
        if type_name in {"task", "event"}:
            options["description"] = positional[0]
        elif type_name == "text":
            options["text"] = positional[0]
        return Command("add", args=[type_name], options=options)

    def _parse_edit(self, tokens: list[str]) -> Command:
        if not tokens:
            raise InvalidCommandError("用法：edit <id> --field value")
        record_id = tokens.pop(0)
        if not record_id.isdigit():
            raise InvalidCommandError("edit 的 ID 必须是正整数")
        options = self._parse_options(tokens)
        if not options:
            raise InvalidCommandError("edit 至少需要一个 --field value")
        return Command("edit", args=[record_id], options=options)

    def _parse_options(self, tokens: list[str]) -> dict[str, str | list[str]]:
        options: dict[str, str | list[str]] = {}
        positional: list[str] = []
        index = 0
        while index < len(tokens):
            token = tokens[index]
            if not token.startswith("--"):
                positional.append(token)
                index += 1
                continue
            key = token[2:].lower().replace("-", "_")
            if not key or index + 1 >= len(tokens) or tokens[index + 1].startswith("--"):
                raise InvalidCommandError(f"选项 --{key} 缺少值")
            value = tokens[index + 1]
            index += 2
            if key in {"deadline", "start", "start_time", "alarm"} and index < len(tokens) and re.fullmatch(r"\d{2}:\d{2}", tokens[index]):
                value = f"{value} {tokens[index]}"
                index += 1
            options[key] = value
        if positional:
            options["_positional"] = positional
        return options  # type: ignore[return-value]
