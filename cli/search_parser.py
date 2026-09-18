"""Recursive-descent parser and evaluator for the US7 search language."""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from model import PIR, parse_datetime
from model.exceptions import SearchParseError


_TOKEN_RE = re.compile(r'\s*("(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|&&|\|\||<=|>=|!=|[()!<>=]|[^\s()!<>=&|]+)')


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1].replace("\\\"", "\"").replace("\\'", "'")
    return value


class SearchNode(ABC):
    @abstractmethod
    def evaluate(self, pir: PIR) -> bool:
        pass


class ComparisonNode(SearchNode):
    def __init__(self, field: str, op: str, value: str) -> None:
        self.field, self.op, self.value = field.lower(), op.lower(), _unquote(value)

    def evaluate(self, pir: PIR) -> bool:
        if self.field == "type":
            actual: Any = pir.get_type()
        else:
            fields = pir.get_fields()
            aliases = {"start": "start_time"}
            key = aliases.get(self.field, self.field)
            if key not in fields:
                return False
            actual = fields[key]
        try:
            if self.op == "contains":
                return self.value.casefold() in str(actual).casefold()
            if isinstance(actual, str) and ("time" in self.field or self.field in {"deadline", "start", "alarm"}):
                actual = parse_datetime(actual)
                expected = parse_datetime(self.value)
            elif isinstance(actual, str):
                expected = self.value
            else:
                expected = self.value
            return _compare(actual, self.op, expected)
        except (TypeError, ValueError, SearchParseError):
            return False


def _compare(actual: Any, op: str, expected: Any) -> bool:
    if isinstance(actual, datetime):
        if not isinstance(expected, datetime):
            expected = parse_datetime(str(expected))
    elif isinstance(expected, datetime):
        actual = parse_datetime(str(actual))
    else:
        actual, expected = str(actual).casefold(), str(expected).casefold()
    if op == "=":
        return actual == expected
    if op == "!=":
        return actual != expected
    if op == "<":
        return actual < expected
    if op == "<=":
        return actual <= expected
    if op == ">":
        return actual > expected
    if op == ">=":
        return actual >= expected
    raise SearchParseError(f"不支持的比较符：{op}")


class LogicNode(SearchNode):
    def __init__(self, op: str, children: list[SearchNode]) -> None:
        self.op, self.children = op, children

    def evaluate(self, pir: PIR) -> bool:
        if self.op == "!":
            return not self.children[0].evaluate(pir)
        if self.op == "&&":
            return all(child.evaluate(pir) for child in self.children)
        if self.op == "||":
            return any(child.evaluate(pir) for child in self.children)
        raise SearchParseError(f"不支持的逻辑符：{self.op}")


class SearchParser:
    def tokenize(self, expression: str) -> list[str]:
        if not isinstance(expression, str) or not expression.strip():
            raise SearchParseError("搜索表达式不能为空")
        tokens: list[str] = []
        pos = 0
        while pos < len(expression):
            match = _TOKEN_RE.match(expression, pos)
            if not match:
                if expression[pos:].strip() == "":
                    break
                raise SearchParseError(f"无法识别搜索表达式附近：{expression[pos:]}")
            tokens.append(match.group(1))
            pos = match.end()
        return tokens

    def parse(self, expression: str) -> SearchNode:
        self.tokens = self.tokenize(expression)
        self.index = 0
        node = self._parse_or()
        if self.index != len(self.tokens):
            raise SearchParseError(f"多余的搜索内容：{' '.join(self.tokens[self.index:])}")
        return node

    def _peek(self) -> str | None:
        return self.tokens[self.index] if self.index < len(self.tokens) else None

    def _take(self) -> str:
        token = self._peek()
        if token is None:
            raise SearchParseError("搜索表达式不完整")
        self.index += 1
        return token

    def _parse_or(self) -> SearchNode:
        node = self._parse_and()
        children = [node]
        while self._peek() == "||":
            self._take()
            children.append(self._parse_and())
        return children[0] if len(children) == 1 else LogicNode("||", children)

    def _parse_and(self) -> SearchNode:
        node = self._parse_not()
        children = [node]
        while self._peek() == "&&":
            self._take()
            children.append(self._parse_not())
        return children[0] if len(children) == 1 else LogicNode("&&", children)

    def _parse_not(self) -> SearchNode:
        if self._peek() == "!":
            self._take()
            return LogicNode("!", [self._parse_not()])
        if self._peek() == "(":
            self._take()
            node = self._parse_or()
            if self._take() != ")":
                raise SearchParseError("缺少右括号")
            return node
        return self._parse_condition()

    def _parse_condition(self) -> SearchNode:
        field = self._take()
        operator = self._take()
        if operator not in {"contains", "=", "!=", "<", "<=", ">", ">="}:
            raise SearchParseError(f"无效的比较符：{operator}")
        value = self._take()
        # Permit unquoted CLI datetimes such as 2026-12-01 20:00.
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value) and self._peek() and re.fullmatch(r"\d{2}:\d{2}", self._peek() or ""):
            value = f"{value} {self._take()}"
        return ComparisonNode(field, operator, value)
