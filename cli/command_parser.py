"""Parse CLI syntax without executing commands or modifying state."""
from __future__ import annotations
from dataclasses import dataclass, field
import re
import shlex
from model.exceptions import InvalidCommandError, ValidationError
from model.factory import FIELD_SCHEMAS, PIRFactory

# Shell words may concatenate quoted and unquoted fragments. Keep their raw
# spelling so a quoted value beginning with -- is not mistaken for an option.
SHELL_WORD = re.compile(r'''(?:[^ \t\r\n'"\\]|\\[\s\S]|"(?:\\[\s\S]|[^"\\])*"|'[^']*')+''')


def split_arguments(tail: str) -> tuple[list[str], list[bool]]:
    values = shlex.split(tail)
    raw_words = SHELL_WORD.findall(tail)
    quoted = ["'" in word or '"' in word or "\\" in word for word in raw_words]
    return values, quoted


@dataclass
class Command:
    name: str
    args: list[str] = field(default_factory=list)
    options: dict[str, str] = field(default_factory=dict)


def positive_id(value: str) -> str:
    if not re.fullmatch(r"[0-9]{1,100}", value) or int(value) < 1:
        raise InvalidCommandError("ID must be a positive integer (up to 100 digits)")
    return value


class CommandParser:
    def parse(self, line: str) -> Command:
        if not isinstance(line, str) or not line.strip():
            raise InvalidCommandError("Command cannot be empty")
        if len(line) > 16384:
            raise InvalidCommandError("Command is too long (maximum 16384 characters)")
        parts = line.strip().split(maxsplit=1)
        name = parts[0].lower()
        tail = parts[1] if len(parts) == 2 else ""
        if name == "search":
            if not tail.strip():
                raise InvalidCommandError("Usage: search <expression>")
            # Keep literal quotes; remove an optional single pair around the whole expression.
            try:
                tokens = shlex.split(tail)
            except ValueError as exc:
                raise InvalidCommandError(f"Unmatched command quote: {exc}") from exc
            if len(tokens) == 1 and tail[0] in "\"'":
                tail = tokens[0]
            return Command(name, [tail])
        try:
            args, quoted = split_arguments(tail)
        except ValueError as exc:
            raise InvalidCommandError(f"Unmatched command quote: {exc}") from exc
        if name == "quit":
            name = "exit"
        if name in {"help", "exit"}:
            if args:
                raise InvalidCommandError(f"{name} does not accept arguments")
            return Command(name)
        if name in {"print", "delete", "save", "load"}:
            if len(args) > 1 or (name in {"delete", "load"} and not args):
                raise InvalidCommandError(f"Usage: {name} <argument>")
            if name in {"delete", "print"} and args and not (name == "print" and args[0].lower() == "all"):
                positive_id(args[0])
            if args and not args[0]:
                raise InvalidCommandError("Argument cannot be empty")
            return Command(name, args)
        if name == "add":
            if not args or args[0].lower() not in FIELD_SCHEMAS:
                raise InvalidCommandError("Usage: add text|task|event|contact ...")
            type_name = args.pop(0).lower()
            quoted.pop(0)
            options = {}
            if type_name != "contact":
                if not args or (args[0].startswith("--") and not quoted[0]):
                    raise InvalidCommandError(f"add {type_name} requires quoted text or description")
                options["text" if type_name == "text" else "description"] = args.pop(0)
                quoted.pop(0)
            parsed = self._options(args, quoted)
            if options.keys() & parsed.keys():
                raise InvalidCommandError("Text or description cannot be specified twice")
            options.update(parsed)
            try:
                options = PIRFactory.normalize_fields(type_name, options)
            except ValidationError as exc:
                raise InvalidCommandError(str(exc)) from exc
            return Command(name, [type_name], options)
        if name == "edit":
            if not args:
                raise InvalidCommandError("Usage: edit <id> --field value")
            record_id = positive_id(args.pop(0))
            quoted.pop(0)
            options = self._options(args, quoted)
            if not options:
                raise InvalidCommandError("edit requires at least one --field value")
            return Command(name, [record_id], options)
        raise InvalidCommandError(f"Unknown command: {name}")

    def _options(self, tokens: list[str], quoted: list[bool]) -> dict[str, str]:
        options = {}
        index = 0
        allowed = set().union(*map(set, FIELD_SCHEMAS.values()))
        while index < len(tokens):
            token = tokens[index]
            if not token.startswith("--"):
                raise InvalidCommandError(f"Unexpected argument: {token}; quote text containing spaces")
            key = token[2:].lower().replace("-", "_")
            key = "start_time" if key == "start" else key
            if key not in allowed:
                raise InvalidCommandError(f"Unknown field: {key}")
            if key in options:
                raise InvalidCommandError(f"Duplicate field: {key}")
            if index + 1 >= len(tokens) or (tokens[index + 1].startswith("--") and not quoted[index + 1]):
                raise InvalidCommandError(f"Field {key} is missing a value")
            value = tokens[index + 1]
            index += 2
            if key in {"deadline", "start_time", "alarm"} and re.fullmatch(r"\d{4}-\d{2}-\d{2}", value) and index < len(tokens) and re.fullmatch(r"\d{2}:\d{2}", tokens[index]):
                value += " " + tokens[index]
                index += 1
            options[key] = value
        return options
