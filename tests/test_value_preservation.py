"""Regressions: whitespace that is not a POSIX separator is record data.

``docs/design.md`` section 4 fixes the word model used by creation and search:
words separate on the POSIX shell set (space, tab, CR, LF) exactly like ``shlex``
and the command parser, so any other whitespace character is part of a word.
FR-02 requires ``add text`` to preserve its content including Unicode, FR-06
requires an edit to store exactly the supplied value, and FR-07/FR-08 require a
criterion to select the records it describes.

The command line and the search expression used to be trimmed with ``str.strip``,
which also removes whitespace that the documented separator set excludes. A value
that ended with such a character was therefore silently shortened on creation and
on search, and an unquoted search could select a different record than the literal
it was given. These tests pin the documented behaviour for the whole excluded set
while keeping the four POSIX separators as separators.
"""
import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from cli import CommandParser, Repl
from model import TextPIR
from model.search import SearchParser
from storage import Storage

ROOT = Path(__file__).resolve().parents[1]

# Whitespace that Python strips but that the POSIX shell word model treats as data.
NON_POSIX_WHITESPACE = ['\u3000', '\u00a0', '\u2009', '\u2028', '\u2029', '\u202f',
                        '\u205f', '\x0b', '\x0c', '\x1c', '\x1f', '\x85']
# The documented separators; a trailing one is padding, not data.
POSIX_SEPARATORS = [' ', '\t']


def run(repl, line):
    with contextlib.redirect_stdout(io.StringIO()):
        return repl.execute(CommandParser().parse(line))


class CommandValueTests(unittest.TestCase):
    def test_trailing_non_posix_whitespace_stays_in_the_parsed_value(self):
        """Design 4: only the POSIX set separates words, so a trailing other space is data."""
        parser = CommandParser()
        for character in NON_POSIX_WHITESPACE:
            with self.subTest(character=hex(ord(character))):
                self.assertEqual(parser.parse('add text b' + character).options['text'], 'b' + character)
                self.assertEqual(parser.parse('edit 1 --text b' + character).options['text'], 'b' + character)
                self.assertEqual(parser.parse('add contact --name n --address a --mobile 0'
                                              + character).options['mobile'], '0' + character)
                # The literal keeps the character; the raw tail is not required to be
                # trimmed, so assert the criterion actually selects the exact record.
                node = SearchParser().parse(parser.parse('search text = b' + character).args[0])
                self.assertTrue(node.evaluate(TextPIR(1, 'b' + character)))
                self.assertFalse(node.evaluate(TextPIR(2, 'b')))

    def test_posix_separators_are_still_trimmed(self):
        """Design 4: space and tab remain separators and never join a value."""
        parser = CommandParser()
        for character in POSIX_SEPARATORS:
            with self.subTest(character=hex(ord(character))):
                self.assertEqual(parser.parse('add text b' + character).options['text'], 'b')
                self.assertEqual(parser.parse('edit 1 --text b' + character).options['text'], 'b')
                command = parser.parse('search text = b' + character)
                node = SearchParser().parse(command.args[0])
                self.assertTrue(node.evaluate(TextPIR(1, 'b')))
                self.assertFalse(node.evaluate(TextPIR(2, 'b ')))
        self.assertEqual(parser.parse('print 1 ').args, ['1'])
        # The outer container is removed as a whole, so the expression inside it
        # behaves exactly like the direct form; padding around it stays padding.
        contained = SearchParser().parse(parser.parse('search "text = b" ').args[0])
        self.assertTrue(contained.evaluate(TextPIR(1, 'b')))
        self.assertFalse(contained.evaluate(TextPIR(2, 'b ')))

    def test_an_argument_that_ends_with_other_whitespace_is_not_padding(self):
        """IR-01/DR-02: IDs and paths are compared as typed, so padding cannot be ignored."""
        from model.exceptions import InvalidCommandError

        parser = CommandParser()
        with self.assertRaises(InvalidCommandError):
            parser.parse('print 1\u3000')
        self.assertEqual(parser.parse('save records.pim\u3000').args, ['records.pim\u3000'])


class SearchExpressionTests(unittest.TestCase):
    def test_tokenizer_keeps_trailing_non_posix_whitespace_in_the_value(self):
        """Design 4 + FR-07: the literal is compared as one word, not silently shortened."""
        parser = SearchParser()
        for character in NON_POSIX_WHITESPACE:
            with self.subTest(character=hex(ord(character))):
                self.assertEqual(parser.tokenize('text = b' + character)[-1], 'b' + character)
                self.assertTrue(parser.parse('text = b' + character).evaluate(TextPIR(1, 'b' + character)))
                self.assertFalse(parser.parse('text = b' + character).evaluate(TextPIR(2, 'b')))

    def test_trailing_posix_separator_is_still_removed(self):
        """Space and tab stay separators for the search expression as well."""
        parser = SearchParser()
        for character in POSIX_SEPARATORS:
            with self.subTest(character=hex(ord(character))):
                self.assertEqual(parser.tokenize('text = b' + character)[-1], 'b')


class ReplValueTests(unittest.TestCase):
    def test_creation_and_edit_store_the_trailing_character(self):
        """FR-02/FR-06: the value the user typed is the value that is stored."""
        for character in NON_POSIX_WHITESPACE:
            with self.subTest(character=hex(ord(character))):
                repl = Repl(confirm=lambda _: True)
                run(repl, 'add text b' + character)
                self.assertEqual(repl.manager.get_pir(1).get_text(), 'b' + character)
                run(repl, 'edit 1 --text c' + character)
                self.assertEqual(repl.manager.get_pir(1).get_text(), 'c' + character)

    def test_search_selects_only_the_record_with_the_same_trailing_character(self):
        """FR-07: an unquoted literal must not select a record that merely prefixes it."""
        for character in NON_POSIX_WHITESPACE:
            with self.subTest(character=hex(ord(character))):
                repl = Repl(confirm=lambda _: True)
                run(repl, 'add text a')
                run(repl, 'add text "a' + character + '"')
                for literal in ['a' + character, '"a' + character + '"']:
                    output = io.StringIO()
                    with contextlib.redirect_stdout(output):
                        repl.execute(CommandParser().parse('search text = ' + literal))
                    self.assertEqual(output.getvalue(), '#2 [text] a' + character + '\n', literal)

    def test_save_and_load_keep_the_trailing_character(self):
        """FR-11/FR-12: value fidelity survives the whole persistence round trip."""
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'values.pim'
            repl = Repl(confirm=lambda _: True)
            run(repl, 'add text b\u3000')
            run(repl, f'save "{path}"')
            run(repl, f'load "{path}"')
            self.assertEqual(repl.manager.get_pir(1).get_text(), 'b\u3000')
            self.assertEqual(Storage.load(path).get_pir(1).get_text(), 'b\u3000')


class RealProcessTests(unittest.TestCase):
    def test_real_cli_preserves_a_trailing_ideographic_space(self):
        """US2/US10: the recorded value and the saved file keep the typed character."""
        commands = 'add text b\u3000\nsearch text = b\u3000\nprint 1\nsave records.pim\nexit\n'
        with tempfile.TemporaryDirectory() as folder:
            result = subprocess.run([sys.executable, str(ROOT / 'main.py')], input=commands,
                                    text=True, encoding='utf-8', capture_output=True, cwd=folder, timeout=20,
                                    env=dict(os.environ, PYTHONIOENCODING='utf-8:strict'))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stderr, '')
            self.assertNotIn('Error:', result.stdout)
            self.assertIn('#1 [text] b\u3000', result.stdout)
            self.assertTrue(result.stdout.count('#1 [text] b\u3000') >= 2, result.stdout)
            saved = json.loads((Path(folder) / 'records.pim').read_text(encoding='utf-8'))
            self.assertEqual(saved['pirs'], [{'id': 1, 'type': 'text', 'text': 'b\u3000'}])


# shlex documents a backslash-escaped ASCII space as a literal value character, so
# `add text tail\ ` must create the same record as `add text "tail "`. The parser
# trimmed the raw command tail before shlex saw it, which deleted the escaped space
# and left a lone backslash; the same trim corrupted a search expression.
ESCAPED_SPACE = '\\ '


class EscapedTrailingSpaceTests(unittest.TestCase):
    """FR-02/FR-06/FR-07: an escaped final space is value data, not padding."""

    def test_creation_and_edit_forms_keep_the_escaped_space(self):
        parser = CommandParser()
        cases = [
            ('add text tail' + ESCAPED_SPACE, 'text', 'tail '),
            ('add task tail' + ESCAPED_SPACE + ' --deadline 2026-01-01 10:00', 'description', 'tail '),
            ('add event tail' + ESCAPED_SPACE + ' --start 2026-01-01 10:00 --alarm 2026-01-01 09:00',
             'description', 'tail '),
            ('add contact --name n' + ESCAPED_SPACE + ' --address a --mobile 0', 'name', 'n '),
            ('add contact --name n --address a --mobile 0' + ESCAPED_SPACE, 'mobile', '0 '),
            ('edit 1 --text tail' + ESCAPED_SPACE, 'text', 'tail '),
            ('edit 1 --description tail' + ESCAPED_SPACE, 'description', 'tail '),
        ]
        for line, field, expected in cases:
            with self.subTest(line=line):
                self.assertEqual(parser.parse(line).options[field], expected)

    def test_escaped_space_is_the_value_of_the_equivalent_quoted_form(self):
        """Design 4: an escaped space and a quoted space are the same shlex word."""
        parser = CommandParser()
        pairs = [
            ('add text tail' + ESCAPED_SPACE, 'add text "tail "'),
            ('add task tail' + ESCAPED_SPACE + ' --deadline 2026-01-01 10:00',
             'add task "tail " --deadline 2026-01-01 10:00'),
            ('add event tail' + ESCAPED_SPACE + ' --start 2026-01-01 10:00 --alarm 2026-01-01 09:00',
             'add event "tail " --start 2026-01-01 10:00 --alarm 2026-01-01 09:00'),
            ('add contact --name n --address a --mobile 0' + ESCAPED_SPACE,
             'add contact --name n --address a --mobile "0 "'),
            ('edit 1 --text tail' + ESCAPED_SPACE, 'edit 1 --text "tail "'),
        ]
        for escaped, quoted in pairs:
            with self.subTest(line=escaped):
                self.assertEqual(parser.parse(escaped).options, parser.parse(quoted).options)

    def test_unescaped_trailing_padding_is_still_padding(self):
        parser = CommandParser()
        self.assertEqual(parser.parse('add text tail ').options['text'], 'tail')
        self.assertEqual(parser.parse('edit 1 --text tail ').options['text'], 'tail')

    def test_a_lone_trailing_backslash_is_still_an_error(self):
        from model.exceptions import InvalidCommandError

        parser = CommandParser()
        for line in ['add text tail' + '\\', 'edit 1 --text tail' + '\\']:
            with self.subTest(line=line):
                with self.assertRaises(InvalidCommandError):
                    parser.parse(line)

    def test_model_tokenizer_decodes_the_escaped_space_once(self):
        from model.exceptions import SearchParseError

        parser = SearchParser()
        self.assertEqual(parser.tokenize('text = tail' + ESCAPED_SPACE),
                         ['text', '=', 'tail' + ESCAPED_SPACE])
        node = parser.parse('text = tail' + ESCAPED_SPACE)
        self.assertTrue(node.evaluate(TextPIR(1, 'tail ')))
        self.assertFalse(node.evaluate(TextPIR(2, 'tail')))
        with self.assertRaises(SearchParseError):
            parser.parse('text = tail' + '\\')

    def test_search_padding_is_ignored_at_the_token_boundary(self):
        parser = SearchParser()
        for expression in ['text = b ', 'text = b\t', ' text = b ']:
            with self.subTest(expression=expression):
                self.assertEqual(parser.tokenize(expression), ['text', '=', 'b'])
                self.assertTrue(parser.parse(expression).evaluate(TextPIR(1, 'b')))
                self.assertFalse(parser.parse(expression).evaluate(TextPIR(2, 'b ')))

    def test_repl_search_with_an_escaped_space_selects_the_exact_record(self):
        repl = Repl(confirm=lambda _: True)
        run(repl, 'add text "tail "')
        run(repl, 'add text tail')
        for line in ['search text = tail' + ESCAPED_SPACE,
                     'search "text = tail' + ESCAPED_SPACE + '"']:
            with self.subTest(line=line):
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    repl.execute(CommandParser().parse(line))
                self.assertEqual(output.getvalue(), '#1 [text] tail \n')

    def test_escaped_space_survives_creation_edit_and_save_load(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'escaped.pim'
            repl = Repl(confirm=lambda _: True)
            run(repl, 'add text tail' + ESCAPED_SPACE)
            self.assertEqual(repl.manager.get_pir(1).get_text(), 'tail ')
            run(repl, 'edit 1 --text head' + ESCAPED_SPACE)
            self.assertEqual(repl.manager.get_pir(1).get_text(), 'head ')
            run(repl, f'save "{path}"')
            run(repl, f'load "{path}"')
            self.assertEqual(repl.manager.get_pir(1).get_text(), 'head ')
            self.assertEqual(Storage.load(path).get_pir(1).get_text(), 'head ')


class EscapedSpaceRealProcessTests(unittest.TestCase):
    def test_real_cli_keeps_an_escaped_trailing_space(self):
        commands = ('add text tail' + ESCAPED_SPACE + '\n'
                    + 'search text = tail' + ESCAPED_SPACE + '\n'
                    + 'print 1\nsave records.pim\nexit\n')
        with tempfile.TemporaryDirectory() as folder:
            result = subprocess.run([sys.executable, str(ROOT / 'main.py')], input=commands,
                                    text=True, encoding='utf-8', capture_output=True, cwd=folder, timeout=20,
                                    env=dict(os.environ, PYTHONIOENCODING='utf-8:strict'))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stderr, '')
            self.assertNotIn('Error:', result.stdout)
            self.assertEqual(result.stdout.count('#1 [text] tail \n'), 2, result.stdout)
            saved = json.loads((Path(folder) / 'records.pim').read_text(encoding='utf-8'))
            self.assertEqual(saved['pirs'], [{'id': 1, 'type': 'text', 'text': 'tail '}])

    def test_real_cli_recovers_after_an_unterminated_escape(self):
        commands = 'add text tail\\\nadd text ok\nprint 1\nsave records.pim\nexit\n'
        with tempfile.TemporaryDirectory() as folder:
            result = subprocess.run([sys.executable, str(ROOT / 'main.py')], input=commands,
                                    text=True, encoding='utf-8', capture_output=True, cwd=folder, timeout=20,
                                    env=dict(os.environ, PYTHONIOENCODING='utf-8:strict'))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stderr, '')
            self.assertIn('Error: Unmatched command quote', result.stdout)
            self.assertIn('#1 [text] ok\n', result.stdout)
            saved = json.loads((Path(folder) / 'records.pim').read_text(encoding='utf-8'))
            self.assertEqual(saved['pirs'], [{'id': 1, 'type': 'text', 'text': 'ok'}])


class LeadingUnicodePathTests(unittest.TestCase):
    """IR-01/DR-02 and design 4: a non-POSIX whitespace starting a path is data.

    ``shlex.split('save \\u00a0records.pim')`` is ``['save', '\\u00a0records.pim']``,
    so the file argument keeps its leading character. The parser split the command
    name with ``str.split(maxsplit=1)``, which folds that character into the
    separator run and silently retargets the command at a different file.
    """

    LEADING_UNICODE = ['\u00a0', '\u3000', '\u2009', '\u202f']

    def test_save_and_load_keep_the_leading_character_of_a_path(self):
        parser = CommandParser()
        for character in self.LEADING_UNICODE:
            with self.subTest(character=hex(ord(character))):
                self.assertEqual(parser.parse('save ' + character + 'records.pim').args,
                                 [character + 'records.pim'])
                self.assertEqual(parser.parse('load ' + character + 'records.pim').args,
                                 [character + 'records.pim'])
                # POSIX padding after the argument is still padding.
                self.assertEqual(parser.parse('save ' + character + 'records.pim ').args,
                                 [character + 'records.pim'])
        self.assertEqual(parser.parse('save records.pim').args, ['records.pim'])

    def test_a_command_of_only_whitespace_is_still_a_domain_error(self):
        from model.exceptions import InvalidCommandError

        parser = CommandParser()
        for line in ['\u00a0', '\u3000', '  \u3000  ']:
            with self.subTest(line=repr(line)):
                with self.assertRaises(InvalidCommandError):
                    parser.parse(line)

    def test_real_cli_saves_and_loads_two_files_with_leading_unicode_paths(self):
        unicode_name = '\u00a0records.pim'
        commands = ('add text plain\nsave records.pim\n'
                    'edit 1 --text unicode\nsave ' + unicode_name + '\n'
                    'load records.pim\nprint 1\nexit\n')
        with tempfile.TemporaryDirectory() as folder:
            result = subprocess.run([sys.executable, str(ROOT / 'main.py')], input=commands,
                                    text=True, encoding='utf-8', capture_output=True, cwd=folder, timeout=20,
                                    env=dict(os.environ, PYTHONIOENCODING='utf-8:strict'))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stderr, '')
            self.assertNotIn('Error:', result.stdout)
            self.assertIn('#1 [text] plain\n', result.stdout)
            plain = json.loads((Path(folder) / 'records.pim').read_text(encoding='utf-8'))
            marked = json.loads((Path(folder) / unicode_name).read_text(encoding='utf-8'))
            self.assertEqual(plain['pirs'][0]['text'], 'plain')
            self.assertEqual(marked['pirs'][0]['text'], 'unicode')
            self.assertEqual(sorted(path.name for path in Path(folder).iterdir()),
                             sorted(['records.pim', unicode_name]))


if __name__ == '__main__':
    unittest.main()
