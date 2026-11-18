"""Regression cases for the search-layer defects found in the audit.

Three defects were reproduced against the pre-fix revision and are pinned here:

1. The search tokenizer separated words on the Unicode-aware ``\\s`` while shlex
   and ``cli.command_parser.SHELL_WORD`` separate only on ' \\t\\r\\n', so text
   that ``add`` stored as a single word could not be found by the same unquoted
   literal.
2. A fully quoted search expression was replaced by its shlex-decoded token, so
   the expression inside the documented outer quote pair was shell-decoded a
   second time and the quoted form silently selected different records than the
   direct form for values containing backslash escapes.
3. ``parse_datetime`` accepted Unicode decimal digits for the year because
   ``strptime``'s %Y matches ``\\d``, although DR-01 defines only the ASCII
   ``YYYY-MM-DD`` pattern.

The contract behind defect 2 is output/pdf/user_manual.pdf: "A search expression may be
entered directly or inside a single outer pair of quotes." The outer pair is
therefore only a container: both entry forms receive the same expression text and
are shell-decoded exactly once. Nesting still switches quote style inside the
pair, because a backslash-escaped inner quote is literal text in either form.
"""
import contextlib
import io
import unittest

from cli import CommandParser, Repl
from model.exceptions import SearchParseError

PARSER = CommandParser()


def search_after_add(add_line, search_line):
    """Create one record in a fresh session, then return the search output."""
    repl = Repl(confirm=lambda _: True)
    with contextlib.redirect_stdout(io.StringIO()):
        repl.execute(PARSER.parse(add_line))
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        try:
            repl.execute(PARSER.parse(search_line))
        except SearchParseError:
            return 'SearchParseError'
    return output.getvalue()


class OuterQuoteContainerTests(unittest.TestCase):
    def test_outer_quoted_backslash_value_is_equivalent_to_the_direct_form(self):
        """User manual 4: either entry form selects the same records.

        The quoted form used to decode the inner text twice, so a stored
        Windows-style path was not found at all by the quoted form.
        """
        stored = 'C:\\Users\\me'
        escaped = stored.replace('\\', '\\\\')
        add = 'add text ' + escaped
        direct = search_after_add(add, 'search text contains ' + escaped)
        outer = search_after_add(add, 'search "text contains ' + escaped + '"')
        self.assertEqual(direct, '#1 [text] ' + stored + '\n')
        self.assertEqual(outer, direct)

    def test_outer_quoted_escaped_operators_are_equivalent_to_the_direct_form(self):
        """User manual 4: escaped operators are literal text in either entry form."""
        add = 'add text hello\\&\\&world'
        direct = search_after_add(add, 'search text = hello\\&\\&world')
        outer = search_after_add(add, 'search "text = hello\\&\\&world"')
        self.assertEqual(direct, '#1 [text] hello&&world\n')
        self.assertEqual(outer, direct)

    def test_outer_quoted_form_never_changes_the_outcome(self):
        """User manual 4: the outer pair groups an expression, it is not a nesting mechanism.

        A backslash-escaped inner quote is literal text in the direct form, so
        the quoted form must reject it in exactly the same way instead of
        decoding it a second time and silently selecting other records.
        """
        add = 'add text "buy milk"'
        self.assertEqual(search_after_add(add, 'search text = \\"buy milk\\"'), 'SearchParseError')
        self.assertEqual(search_after_add(add, 'search "text = \\"buy milk\\""'), 'SearchParseError')

    def test_documented_nested_quotation_styles_still_work(self):
        """User manual 4: nest quotations by switching quote style inside the outer pair."""
        add = 'add text "hello world"'
        for search_line in ["search 'text contains \"hello world\"'",
                            'search "text contains \'hello world\'"']:
            with self.subTest(search_line=search_line):
                self.assertEqual(search_after_add(add, search_line), '#1 [text] hello world\n')

    def test_outer_quoted_form_keeps_rejecting_unmatched_quotes(self):
        """User manual 7: malformed quoted searches report an error and leave the session usable."""
        from model.exceptions import InvalidCommandError

        with self.assertRaises(InvalidCommandError):
            PARSER.parse('search "bad')
        repl = Repl(confirm=lambda _: True)
        with contextlib.redirect_stdout(io.StringIO()):
            repl.execute(PARSER.parse('add text keep'))
        with self.assertRaises(SearchParseError):
            repl.execute(PARSER.parse('search ""'))
        self.assertEqual(repl.manager.get_pir(1).get_text(), 'keep')


class SearchSeparatorTests(unittest.TestCase):
    def test_search_separators_match_the_command_word_rules(self):
        """Design 4: the search tokenizer preserves whole shell words.

        shlex and SHELL_WORD separate words only on ' \\t\\r\\n', so each value
        below is one word when it is created and must stay one word when it is
        searched without quotes.
        """
        for separator in ['\u00a0', '\u1680', '\u2009', '\u2028', '\u2029', '\u202f',
                          '\u205f', '\u3000', '\x0b', '\x0c', '\x1c', '\x1f', '\x85']:
            with self.subTest(separator=hex(ord(separator))):
                value = 'a' + separator + 'b'
                found = search_after_add('add text ' + value, 'search text = ' + value)
                self.assertEqual(found, '#1 [text] ' + value + '\n')

    def test_shell_separators_still_split_words(self):
        """The POSIX set ' \\t\\r\\n' still separates words in both layers."""
        add = 'add text "two words"'
        expected = '#1 [text] two words\n'
        self.assertEqual(search_after_add(add, 'search text = "two words"'), expected)
        self.assertEqual(search_after_add(add, 'search text contains two\\ words'), expected)


class TimestampDigitTests(unittest.TestCase):
    def test_timestamp_digits_are_ascii(self):
        """DR-01: accepted timestamps use the ASCII pattern YYYY-MM-DD[ HH:MM].

        Python's strptime accepts any Unicode decimal digit for %Y, so a value
        with an Arabic-Indic or fullwidth year used to be stored as 2026-01-01
        even though DR-01 defines only the ASCII form.
        """
        from model.exceptions import ValidationError
        from model.pir import parse_datetime

        for value in ['\u0662\u0660\u0662\u0666-01-01', '\uff12\uff10\uff12\uff16-01-01',
                      '\u0662\u0660\u0662\u0666-01-01 09:00', '\u0662\u0660\u0662\u0666-01-01T00:00:00']:
            with self.subTest(value=value), self.assertRaises(ValidationError):
                parse_datetime(value)
        self.assertEqual(str(parse_datetime('2026-01-01')), '2026-01-01 00:00:00')
        self.assertEqual(str(parse_datetime('2026-01-01T09:00:00')), '2026-01-01 09:00:00')


if __name__ == '__main__':
    unittest.main()
