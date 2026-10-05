"""Validated search criteria with recursive descent: ! > && > ||."""
from __future__ import annotations
from abc import ABC, abstractmethod
import operator
import re
import shlex
from .pir import PIR, parse_datetime
from .exceptions import SearchParseError, ValidationError

TEXT_FIELDS = {"type", "text", "description", "name", "address", "mobile"}
TIME_FIELDS = {"deadline", "start", "start_time", "alarm"}
OPERATORS = {"=": operator.eq, "!=": operator.ne, "<": operator.lt,
             "<=": operator.le, ">": operator.gt, ">=": operator.ge}
# Match shlex quoting: single quotes keep every backslash literal, while a
# double-quoted escape may span any character, including a newline.
TOKEN = re.compile(r'''\s*("(?:\\[\s\S]|[^"\\])*"|'[^']*'|&&|\|\||<=|>=|!=|[()!<>=]|[^\s()!<>=&|'"\\]+)''')


class SearchNode(ABC):
    @abstractmethod
    def evaluate(self, pir: PIR) -> bool:
        """Return whether this record satisfies the criterion."""


class ComparisonNode(SearchNode):
    def __init__(self, field: str, op: str, value: str) -> None:
        self.field, self.op = field.lower(), op.lower()
        if self.field not in TEXT_FIELDS | TIME_FIELDS:
            raise SearchParseError(f"Unknown search field: {field}")
        allowed = set(OPERATORS) if self.field in TIME_FIELDS else {"contains", "=", "!="}
        if self.field == "type":
            allowed = {"=", "!="}
        if self.op not in allowed:
            raise SearchParseError(f"Field {field} does not support operator {op}")
        self.value = value
        try:
            self.expected = parse_datetime(value) if self.field in TIME_FIELDS else value.casefold()
        except ValidationError as exc:
            raise SearchParseError(str(exc)) from exc
        if self.field == "type" and self.expected not in {"text", "task", "event", "contact"}:
            raise SearchParseError(f"Unknown PIR type: {value}")

    def evaluate(self, pir: PIR) -> bool:
        key = "start_time" if self.field == "start" else self.field
        if key == "type":
            actual = pir.get_type()
        else:
            fields = pir.get_fields()
            if key not in fields:
                return False
            actual = fields[key]
        actual = parse_datetime(actual) if self.field in TIME_FIELDS else actual.casefold()
        if self.op == "contains":
            return self.expected in actual
        return OPERATORS[self.op](actual, self.expected)


class LogicNode(SearchNode):
    def __init__(self, op: str, children: list[SearchNode]) -> None:
        if op not in {"!", "&&", "||"} or not children or (op == "!" and len(children) != 1):
            raise SearchParseError("Invalid logic node")
        self.op, self.children = op, tuple(children)

    def evaluate(self, pir: PIR) -> bool:
        if self.op == "!":
            return not self.children[0].evaluate(pir)
        if self.op == "&&":
            return all(child.evaluate(pir) for child in self.children)
        return any(child.evaluate(pir) for child in self.children)


class SearchParser:
    def tokenize(self, expression: str) -> list[str]:
        if not isinstance(expression, str) or not expression.strip():
            raise SearchParseError("Search expression cannot be empty")
        if len(expression) > 8192:
            raise SearchParseError("Search expression is too long (maximum 8192 characters)")
        tokens, pos = [], 0
        expression = expression.strip()
        while pos < len(expression):
            match = TOKEN.match(expression, pos)
            if not match:
                raise SearchParseError(f"Invalid character or unterminated quote at position {pos + 1}")
            tokens.append(match.group(1))
            pos = match.end()
        return tokens

    def parse(self, expression: str) -> SearchNode:
        tokens = self.tokenize(expression)
        # Parsing state belongs to this call, allowing parser reuse after errors.
        index = 0

        def peek():
            return tokens[index] if index < len(tokens) else None

        def take():
            nonlocal index
            token = peek()
            if token is None:
                raise SearchParseError("Incomplete search expression")
            index += 1
            return token

        def condition():
            field, op, value = take(), take(), take()
            if value in {"(", ")", "!", "&&", "||"} | set(OPERATORS):
                raise SearchParseError("Missing comparison value; quote special characters")
            if value[0] in "\"'":
                try:
                    value = shlex.split(value)[0]
                except ValueError as exc:
                    raise SearchParseError(f"Invalid quoted search value: {exc}") from exc
            elif re.fullmatch(r"\d{4}-\d{2}-\d{2}", value) and re.fullmatch(r"\d{2}:\d{2}", peek() or ""):
                value += " " + take()
            return ComparisonNode(field, op, value)

        def parse_not(depth):
            if depth > 64:
                raise SearchParseError("Search nesting is too deep (maximum 64 levels)")
            if peek() == "!":
                take()
                return LogicNode("!", [parse_not(depth + 1)])
            if peek() == "(":
                take()
                node = parse_or(depth + 1)
                if take() != ")":
                    raise SearchParseError("Missing closing parenthesis")
                return node
            return condition()

        def parse_and(depth):
            children = [parse_not(depth)]
            while peek() == "&&":
                take()
                children.append(parse_not(depth))
            return children[0] if len(children) == 1 else LogicNode("&&", children)

        def parse_or(depth):
            children = [parse_and(depth)]
            while peek() == "||":
                take()
                children.append(parse_and(depth))
            return children[0] if len(children) == 1 else LogicNode("||", children)

        node = parse_or(0)
        if peek() is not None:
            raise SearchParseError(f"Unexpected search content: {peek()}")
        return node
