import unittest

from cli.search_parser import SearchParser
from model import TaskPIR, TextPIR, SearchParseError


class SearchParserTests(unittest.TestCase):
    def setUp(self):
        self.parser = SearchParser()
        self.task = TaskPIR(1, "Submit report", "2026-11-19 20:00")
        self.note = TextPIR(2, "buy milk")

    def test_contains_and_time_comparison(self):
        """US7: text containment and earlier-than comparisons match expected records."""
        self.assertTrue(self.parser.parse('description contains "report"').evaluate(self.task))
        self.assertTrue(self.parser.parse("deadline < 2026-12-01").evaluate(self.task))

    def test_logic_precedence_and_parentheses(self):
        """US7: OR combines alternatives and NOT reverses a type condition."""
        node = self.parser.parse('type = task && deadline < 2026-12-01 || text contains "milk"')
        self.assertTrue(node.evaluate(self.task))
        self.assertTrue(node.evaluate(self.note))
        self.assertFalse(self.parser.parse("! type = task").evaluate(self.task))

    def test_invalid_expression(self):
        """Missing comparison values raise SearchParseError."""
        with self.assertRaises(SearchParseError):
            self.parser.parse("type =")


if __name__ == "__main__":
    unittest.main()
