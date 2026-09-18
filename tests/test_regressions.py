"""Regression cases for defects found in the requirement audit."""

import contextlib
import io
import unittest
from unittest.mock import patch

from cli import Repl
from cli.command_parser import CommandParser
from cli.search_parser import SearchParser
from controller import PIMManager, PIRFactory
from model import ValidationError, SearchParseError


class RegressionTests(unittest.TestCase):
    def test_invalid_ids_do_not_end_session(self):
        """Bad print/delete IDs and missing arguments must leave REPL usable."""
        repl = Repl()
        output = io.StringIO()
        with patch('builtins.input', side_effect=['print abc', 'delete abc', 'delete', 'exit']), contextlib.redirect_stdout(output):
            repl.run()
        self.assertEqual(output.getvalue().count('Error:'), 3)
        self.assertIn('Goodbye.', output.getvalue())

    def test_unknown_edit_field_is_rejected_atomically(self):
        """A typo must raise ValidationError and preserve the existing note."""
        manager = PIMManager()
        manager.add_pir(PIRFactory.create('text', {'text': 'original'}))
        before = manager.to_dict()
        with self.assertRaises(ValidationError):
            manager.edit_pir(1, {'text': 'changed', 'unknown': 'value'})
        self.assertEqual(manager.to_dict(), before)

    def test_cli_search_preserves_quoted_text(self):
        """A multiword quoted literal must survive command parsing."""
        command = CommandParser().parse('search text contains "hello world"')
        node = SearchParser().parse(command.args[0])
        self.assertTrue(node.evaluate(PIRFactory.create('text', {'text': 'Hello World!'})))

    def test_bad_search_is_rejected_without_records(self):
        """Invalid fields/operators/dates must be caught before evaluation."""
        for expression in ['unknown = x', 'deadline contains 2026', 'deadline < bad-date']:
            with self.subTest(expression=expression), self.assertRaises(SearchParseError):
                SearchParser().parse(expression)
