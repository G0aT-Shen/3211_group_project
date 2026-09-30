"""Regression cases for defects found in the requirement audit."""

import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from cli import Repl
from cli.command_parser import CommandParser
from cli.search_parser import SearchParser
from controller import PIMManager, PIRFactory
from model import ValidationError, SearchParseError


class RegressionTests(unittest.TestCase):
    def test_malformed_quoted_search_keeps_unsaved_session_alive(self):
        """A nested quote error must preserve the note and allow save in the real process."""
        with tempfile.TemporaryDirectory() as folder:
            commands = ['add text original', 'search "=||\'\\\'\'"',
                        'print 1', 'save kept.pim', 'exit']
            result = subprocess.run(
                [sys.executable, str(Path(__file__).resolve().parents[1] / 'main.py')],
                input='\n'.join(commands) + '\n', text=True, capture_output=True,
                cwd=folder, timeout=15)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stderr, '')
            self.assertEqual(result.stdout.count('Error:'), 1)
            self.assertIn('#1 [text] original', result.stdout)
            self.assertTrue((Path(folder) / 'kept.pim').is_file())
            saved = json.loads((Path(folder) / 'kept.pim').read_text(encoding='utf-8'))
            self.assertEqual(saved['pirs'][0]['text'], 'original')
        with self.assertRaises(SearchParseError):
            SearchParser().parse("text = '\\''")

    def test_quoted_option_like_values_roundtrip_through_cli(self):
        """Quoted double-dash content remains literal across add, edit, save and load."""
        repl = Repl(confirm=lambda _: True)
        with tempfile.TemporaryDirectory() as folder, contextlib.redirect_stdout(io.StringIO()):
            commands = ['add text "--todo"',
                        'add task "--work" --deadline 2026-01-01',
                        'add contact --name "--Alice" --address "--road" --mobile "--0123"',
                        'edit 1 --text "--archived"',
                        'edit 2 --description "--deadline"',
                        'add text pre"--quoted"post',
                        'add text """--joined"',
                        'add event "--meeting" --start 2026-01-01 --alarm 2026-01-01',
                        'add text a\u00a0b', 'edit 7 --text "--unicode\u3000space"',
                        r'add text \--escaped']
            for command in commands:
                repl.execute(CommandParser().parse(command))
            before = repl.manager.to_dict()
            path = Path(folder) / 'values.pim'
            repl.execute(CommandParser().parse(f'save "{path}"'))
            repl.execute(CommandParser().parse(f'load "{path}"'))
            self.assertEqual(repl.manager.to_dict(), before)
            self.assertEqual(repl.manager.get_pir(1).get_text(), '--archived')
            self.assertEqual(repl.manager.get_pir(2).get_description(), '--deadline')
            self.assertEqual(repl.manager.get_pir(3).get_mobile(), '--0123')
            self.assertEqual(repl.manager.get_pir(4).get_text(), 'pre--quotedpost')
            self.assertEqual(repl.manager.get_pir(5).get_text(), '--joined')
            self.assertEqual(repl.manager.get_pir(6).get_description(), '--meeting')
            self.assertEqual(repl.manager.get_pir(7).get_text(), '--unicode\u3000space')
            self.assertEqual(repl.manager.get_pir(8).get_text(), '--escaped')

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
