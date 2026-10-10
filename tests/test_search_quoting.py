"""Search literals must preserve the command parser's POSIX quoting rules."""
import contextlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from cli import CommandParser, Repl
from model import SearchParseError, TextPIR
from model.search import SearchParser
from storage import Storage


class SearchQuotingTests(unittest.TestCase):
    def test_escaped_and_concatenated_words_match_command_text(self):
        """Creation and search decode shell escapes and quote fragments consistently."""
        cases = [(r'hello\ world', 'hello world'),
                 ('"hello"world', 'helloworld'),
                 ("'buy '\"milk\"", 'buy milk'),
                 (r'hello\&\&world', 'hello&&world'),
                 (r'C:\\work\\', 'C:\\work\\')]
        for literal, expected in cases:
            with self.subTest(literal=literal):
                command = CommandParser().parse('add text ' + literal)
                self.assertEqual(command.options['text'], expected)
                node = SearchParser().parse('text = ' + literal)
                self.assertTrue(node.evaluate(TextPIR(text=expected)))
                self.assertFalse(node.evaluate(TextPIR(text=expected + ' different')))

    def test_escaped_operators_remain_literal_inside_compound_search(self):
        """Escaped ampersands belong to text; unescaped OR still combines criteria."""
        node = SearchParser().parse(r'text = hello\&\&world || text = "other"')
        for text, expected in [('hello&&world', True), ('other', True), ('world', False)]:
            with self.subTest(text=text):
                self.assertEqual(node.evaluate(TextPIR(text=text)), expected)

    def test_single_quoted_backslashes_are_literal(self):
        """Trailing backslashes and quoted syntax remain searchable record content."""
        for literal in [r"'C:\'", r"'C:\work\'", r"'\\server\share\'",
                        r"'C:\&&()\'", "'backslash\\\nnext'"]:
            with self.subTest(literal=literal):
                command = CommandParser().parse('add text ' + literal)
                record = TextPIR(text=command.options['text'])
                node = SearchParser().parse('text = ' + literal)
                self.assertTrue(node.evaluate(record))

    def test_double_quoted_escaped_newline_matches_command_text(self):
        """The model parser accepts escaped newlines already accepted in commands."""
        literal = '"backslash\\\nnext"'
        command = CommandParser().parse('add text ' + literal)
        node = SearchParser().parse('text = ' + literal)
        self.assertTrue(node.evaluate(TextPIR(text=command.options['text'])))

    def test_backslash_cannot_escape_a_single_quote(self):
        """Correct literal backslash handling must not admit malformed quotations."""
        for expression in ["text = '\\''", "text = 'one\\'two'", "text = 'unclosed\\"]:
            with self.subTest(expression=expression), self.assertRaises(SearchParseError):
                SearchParser().parse(expression)

    def test_repl_searches_paths_and_keeps_them_after_save_load(self):
        """Direct and outer-quoted searches find a path and preserve the live session."""
        repl = Repl()
        value = 'C:\\work\\'
        expression = "text = '" + value + "'"
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'paths.pim'
            commands = ["add text '" + value + "'", 'search ' + expression,
                        'search "' + expression + '"', f'save "{path}"',
                        f'load "{path}"', 'search ' + expression, 'exit']
            with patch('builtins.input', side_effect=commands), \
                    contextlib.redirect_stdout(io.StringIO()) as output:
                repl.run()
            self.assertNotIn('Error:', output.getvalue())
            self.assertEqual(output.getvalue().count('#1 [text] ' + value), 3)
            self.assertEqual(Storage.load(path).get_pir(1).get_text(), value)
            self.assertIn('Goodbye.', output.getvalue())
