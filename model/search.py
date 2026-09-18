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
TOKEN = re.compile(r'''\s*("(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|&&|\|\||<=|>=|!=|[()!<>=]|[^\s()!<>=&|'"\\]+)''')


class SearchNode(ABC):
    @abstractmethod
    def evaluate(self, pir: PIR) -> bool:
        """Return whether this record satisfies the criterion."""


class ComparisonNode(SearchNode):
    def __init__(self, field: str, op: str, value: str) -> None:
        self.field, self.op = field.lower(), op.lower()
        if self.field not in TEXT_FIELDS | TIME_FIELDS:
            raise SearchParseError(f"未知搜索字段：{field}")
        allowed = set(OPERATORS) if self.field in TIME_FIELDS else {"contains", "=", "!="}
        if self.field == "type":
            allowed = {"=", "!="}
        if self.op not in allowed:
            raise SearchParseError(f"字段 {field} 不支持操作符 {op}")
        self.value = value
        try:
            self.expected = parse_datetime(value) if self.field in TIME_FIELDS else value.casefold()
        except ValidationError as exc:
            raise SearchParseError(str(exc)) from exc
        if self.field == "type" and self.expected not in {"text", "task", "event", "contact"}:
            raise SearchParseError(f"未知 PIR 类型：{value}")

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
            raise SearchParseError("无效逻辑节点")
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
            raise SearchParseError("搜索表达式不能为空")
        if len(expression) > 8192:
            raise SearchParseError("搜索表达式过长（最多 8192 字符）")
        tokens, pos = [], 0
        expression = expression.strip()
        while pos < len(expression):
            match = TOKEN.match(expression, pos)
            if not match:
                raise SearchParseError(f"无效字符或未闭合引号（位置 {pos + 1}）")
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
                raise SearchParseError("搜索表达式不完整")
            index += 1
            return token

        def condition():
            field, op, value = take(), take(), take()
            if value in {"(", ")", "!", "&&", "||"} | set(OPERATORS):
                raise SearchParseError("缺少比较值；特殊字符须用引号包裹")
            if value[0] in "\"'":
                value = shlex.split(value)[0]
            elif re.fullmatch(r"\d{4}-\d{2}-\d{2}", value) and re.fullmatch(r"\d{2}:\d{2}", peek() or ""):
                value += " " + take()
            return ComparisonNode(field, op, value)

        def parse_not(depth):
            if depth > 64:
                raise SearchParseError("搜索嵌套过深（最多 64 层）")
            if peek() == "!":
                take()
                return LogicNode("!", [parse_not(depth + 1)])
            if peek() == "(":
                take()
                node = parse_or(depth + 1)
                if take() != ")":
                    raise SearchParseError("缺少右括号")
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
            raise SearchParseError(f"多余的搜索内容：{peek()}")
        return node
