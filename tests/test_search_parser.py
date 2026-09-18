import unittest

from cli.search_parser import SearchParser
from model import TaskPIR, TextPIR


class SearchParserTests(unittest.TestCase):
    def setUp(self):
        self.parser = SearchParser()
        self.task = TaskPIR(1, "Submit report", "2026-11-19 20:00")
        self.note = TextPIR(2, "buy milk")

    def test_contains_and_time_comparison(self):
        self.assertTrue(self.parser.parse('description contains "report"').evaluate(self.task))
        self.assertTrue(self.parser.parse("deadline < 2026-12-01").evaluate(self.task))

    def test_logic_precedence_and_parentheses(self):
        node = self.parser.parse('type = task && deadline < 2026-12-01 || text contains "milk"')
        self.assertTrue(node.evaluate(self.task))
        self.assertTrue(node.evaluate(self.note))
        self.assertFalse(self.parser.parse("! type = task").evaluate(self.task))

    def test_invalid_expression(self):
        with self.assertRaises(Exception):
            self.parser.parse("type =")


if __name__ == "__main__":
    unittest.main()
