"""Requirement and boundary tests; each test states the observable contract."""
import contextlib
import io
import json
from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from cli import Command, CommandParser, Repl
from model import (PIR, TextPIR, TaskPIR, EventPIR, ContactPIR, PIMManager,
                   PIRFactory, ValidationError, InvalidCommandError, SearchParseError,
                   StorageError, PIRNotFoundError, parse_datetime)
from model.search import SearchParser, LogicNode
from storage import Storage
from storage.storage import pim_path
from view import Printer

CASES = {
    'text': {'text': 'Hello world && milk'},
    'task': {'description': 'Submit Report', 'deadline': '2026-11-19 20:00'},
    'event': {'description': 'Team meeting', 'start_time': '2026-10-12 09:00', 'alarm': '2026-10-12 08:30'},
    'contact': {'name': 'Alice', 'address': 'Hong Kong', 'mobile': '+852 01234567'},
}


def records():
    return [PIRFactory.create(kind, fields, index) for index, (kind, fields) in enumerate(CASES.items(), 1)]


class ModelContractTests(unittest.TestCase):
    def test_every_record_round_trips_and_prints_all_fields(self):
        """US1-5/8/11: all types retain IDs, type and every field on restoration."""
        for record in records():
            with self.subTest(kind=record.get_type()):
                self.assertEqual(PIR.from_dict(record.to_dict()).to_dict(), record.to_dict())
                self.assertIn(str(record.get_id()), str(record))
                self.assertIn(record.get_type(), str(record))
                for value in record.get_fields().values():
                    self.assertIn(value.replace('T', ' ')[:16] if 'T' in value and value[:4].isdigit() else value, str(record))

    def test_getters(self):
        """Public getters must expose original content and parsed local times."""
        text, task, event, contact = records()
        self.assertEqual(text.get_text(), CASES['text']['text'])
        self.assertEqual(task.get_description(), 'Submit Report')
        self.assertEqual(event.get_description(), 'Team meeting')
        self.assertEqual(event.get_alarm(), datetime(2026, 10, 12, 8, 30))
        self.assertEqual(contact.get_name(), 'Alice')
        self.assertEqual(contact.get_address(), 'Hong Kong')
        self.assertEqual(contact.get_mobile(), '+852 01234567')

    def test_model_is_abstract_and_records_are_immutable(self):
        """Unvalidated mutation must not bypass model invariants."""
        with self.assertRaises(TypeError):
            PIR()
        note = TextPIR(text='original')
        with self.assertRaises(AttributeError):
            note.text = ''
        with self.assertRaises(AttributeError):
            del note.text
        fields = note.get_fields()
        fields['text'] = 'mutated'
        self.assertEqual(note.get_text(), 'original')

    def test_required_fields_reject_invalid_values(self):
        """Every required string/date field rejects null, wrong type and empty input."""
        for kind, fields in CASES.items():
            for key in fields:
                for value in [None, '', '   ', 12, [], True]:
                    with self.subTest(kind=kind, key=key, value=value), self.assertRaises(ValidationError):
                        PIRFactory.create(kind, dict(fields, **{key: value}))

    def test_direct_constructor_validation(self):
        """Direct model construction applies the same required-field rules."""
        for constructor in [lambda: TaskPIR(description=''), lambda: TaskPIR(description='x'),
                            lambda: EventPIR(description=''), lambda: EventPIR(description='x'),
                            lambda: ContactPIR(name='', address='a', mobile='1')]:
            with self.assertRaises(ValidationError):
                constructor()
        for record_id in [0, -1, True, 1.2, '1']:
            with self.subTest(record_id=record_id), self.assertRaises(ValidationError):
                TextPIR(record_id, 'x')

    def test_dates_are_strict_and_minute_precision(self):
        """Dates support leap days, date-only midnight and ISO persistence, without timezones."""
        for text in ['2024-02-29', '2024-02-29 00:00', '2024-02-29T00:00', '2024-02-29T00:00:00']:
            self.assertEqual(parse_datetime(text), datetime(2024, 2, 29))
        self.assertEqual(parse_datetime(datetime(2026, 1, 1)), datetime(2026, 1, 1))
        for value in ['2026-02-29', '2026-13-01', '2026-01-01 24:00', '2026-1-1',
                      '2026-01-01T00:00:01', '2026-01-01T00:00Z', datetime.now(timezone.utc),
                      datetime(2026, 1, 1, microsecond=1), object()]:
            with self.subTest(value=value), self.assertRaises(ValidationError):
                parse_datetime(value)

    def test_factory_rejects_unknown_duplicate_missing_and_wrong_fields(self):
        """Typos and ambiguous aliases fail explicitly rather than being ignored."""
        cases = [('other', {}), (None, {}), ('text', []), ('text', {1: 'x'}),
                 ('text', {'text': 'x', 'extra': 'y'}), ('task', {'description': 'x'}),
                 ('event', dict(CASES['event'], start='2026-01-01'))]
        for kind, fields in cases:
            with self.subTest(kind=kind, fields=fields), self.assertRaises(ValidationError):
                PIRFactory.create(kind, fields)
        event = PIRFactory.create('EVENT', {'description': 'x', 'start': '2026-01-01', 'alarm': '2026-01-01'})
        self.assertEqual(event.get_start_time(), datetime(2026, 1, 1))

    def test_persisted_record_requires_valid_id_and_type(self):
        """Malformed saved records consistently raise a domain validation error."""
        for data in [[], {}, {'id': 1}, {'type': 'text'}, {'id': None, 'type': 'text'},
                     {'id': True, 'type': 'text'}, {'id': 1, 'type': 42},
                     {'id': 1, 'type': 'text', 'text': 'x', 'unknown': 1}]:
            with self.subTest(data=data), self.assertRaises(ValidationError):
                PIRFactory.from_dict(data)

    def test_manager_snapshot_and_id_integrity(self):
        """Records and returned collections cannot mutate manager state or reuse deleted IDs."""
        manager = PIMManager(records(), next_id=9)
        self.assertEqual(manager.next_id, 9)
        with self.assertRaises(TypeError):
            manager.pirs[1] = TextPIR(1, 'bad')
        manager.list_all().clear()
        self.assertEqual(len(manager.pirs), 4)
        manager.delete_pir(4)
        restored = PIMManager.from_dict(manager.to_dict())
        self.assertEqual(restored.add_pir(TextPIR(text='new')).get_id(), 9)

    def test_manager_rejects_bad_ids_and_duplicates(self):
        """Invalid IDs, duplicate initial IDs and preassigned new records fail predictably."""
        for next_id in [0, -1, True, '1']:
            with self.assertRaises(ValidationError):
                PIMManager(next_id=next_id)
        for initial in [[TextPIR(text='x')], [object()], [TextPIR(1, 'x'), TextPIR(1, 'y')]]:
            with self.assertRaises(ValidationError):
                PIMManager(initial)
        manager = PIMManager()
        for value in [True, 0, -1, '1', 1.2]:
            with self.assertRaises(ValidationError):
                manager.get_pir(value)
        for value in [object(), TextPIR(1, 'x')]:
            with self.assertRaises(ValidationError):
                manager.add_pir(value)
        with self.assertRaises(PIRNotFoundError):
            manager.delete_pir(1)

    def test_all_fields_edit_and_failed_edits_are_atomic(self):
        """US6: every field supports edit; a failing multi-field edit changes nothing."""
        manager = PIMManager(records())
        for pir in manager.list_all():
            for key, value in pir.get_fields().items():
                new = '2026-12-01 12:00' if key in {'deadline', 'start_time', 'alarm'} else value + ' updated'
                manager.edit_pir(pir.get_id(), key, new)
                self.assertNotEqual(manager.get_pir(pir.get_id()).get_fields()[key], value)
        manager.edit_pir(3, {'start': '2026-12-02'})
        self.assertEqual(manager.get_pir(3).get_start_time(), datetime(2026, 12, 2))
        before = manager.to_dict()
        for updates in [{}, {'description': 'changed', 'deadline': 'bad'}, {'unknown': 'x'}]:
            with self.assertRaises(ValidationError):
                manager.edit_pir(2, updates)
            self.assertEqual(manager.to_dict(), before)

    def test_strict_file_schema(self):
        """Invalid schema, duplicate IDs and non-monotonic next_id must not load."""
        valid = PIMManager(records()).to_dict()
        invalid = [[], {}, dict(valid, extra=1), dict(valid, schema_version=True),
                   dict(valid, schema_version=2), dict(valid, pirs={}),
                   dict(valid, next_id=4), dict(valid, next_id=True),
                   dict(valid, pirs=[valid['pirs'][0], valid['pirs'][0]])]
        for data in invalid:
            with self.subTest(data=data), self.assertRaises(ValidationError):
                PIMManager.from_dict(data)


class SearchContractTests(unittest.TestCase):
    def test_contains_on_all_text_fields(self):
        """US7: all textual fields support Unicode, casefold and multiword contains."""
        manager = PIMManager(records())
        for field, value, expected in [('text', 'world &&', [1]), ('description', 'REPORT', [2]),
                                        ('name', 'ALICE', [4]), ('address', 'hong kong', [4]), ('mobile', '0123', [4])]:
            node = SearchParser().parse(f'{field} contains "{value}"')
            self.assertEqual([p.get_id() for p in manager.search(node)], expected)

    def test_time_operators_on_every_time_field(self):
        """US7: before/after/equality and extended comparisons use dates, not text ordering."""
        manager = PIMManager(records())
        for field, record_id, date in [('deadline', 2, '2026-11-19 20:00'), ('start', 3, '2026-10-12 09:00'), ('alarm', 3, '2026-10-12 08:30')]:
            for op, expected in [('=', True), ('!=', False), ('<', False), ('>', False), ('<=', True), ('>=', True)]:
                node = SearchParser().parse(f'{field} {op} "{date}"')
                self.assertEqual(node.evaluate(manager.get_pir(record_id)), expected)
            self.assertTrue(SearchParser().parse(f'{field} > 2026-01-01').evaluate(manager.get_pir(record_id)))
            self.assertTrue(SearchParser().parse(f'{field} < 2027-01-01').evaluate(manager.get_pir(record_id)))

    def test_boolean_precedence_parentheses_and_missing_fields(self):
        """AND binds before OR; NOT and parentheses change the actual result set."""
        manager = PIMManager(records())
        expressions = {
            'type = text || type = task && description contains missing': [1],
            '(type = text || type = task) && description contains missing': [],
            '!(type = event || type = contact)': [1, 2],
            '!!type = event': [3],
            'deadline != 2027-01-01': [2],
            '!deadline = 2027-01-01': [1, 2, 3, 4],
            'type != contact && text = "hello world && milk"': [1],
            'text != "x"': [1],
            'start_time = 2026-10-12 09:00': [3],
        }
        for expr, expected in expressions.items():
            with self.subTest(expr=expr):
                self.assertEqual([p.get_id() for p in manager.search(SearchParser().parse(expr))], expected)

    def test_invalid_search_and_resource_limits(self):
        """Malformed quotes, operators, fields and excessive nesting are rejected before searching."""
        for expr in ['', None, 'type =', '(type = text', '(type = text text', 'type = text)',
                     'text contains "unterminated', 'type = text & type = task', 'type = unknown',
                     'text < x', 'type contains text', 'deadline contains 2026', 'x = y',
                     'text = &&', 'text ??? x', '!' * 66 + 'type = text', 'x' * 8193,
                     'deadline < 2026-02-30']:
            with self.subTest(expr=expr), self.assertRaises(SearchParseError):
                SearchParser().parse(expr)
        for op, children in [('?', []), ('!', []), ('!', [1, 2])]:
            with self.assertRaises(SearchParseError):
                LogicNode(op, children)

    def test_parser_reuse_after_error_and_quoted_specials(self):
        """Parser state is per call and quoted syntax is literal data."""
        parser = SearchParser()
        with self.assertRaises(SearchParseError):
            parser.parse('(')
        note = TextPIR(text='a "quote" (x) && y')
        self.assertTrue(parser.parse('text contains \'"quote" (x) &&\'  ').evaluate(note))
        self.assertTrue(parser.parse('text contains ""').evaluate(note))


class CommandContractTests(unittest.TestCase):
    def test_valid_commands_and_aliases(self):
        """Quoted text, unquoted datetime pairs and documented aliases parse correctly."""
        parser = CommandParser()
        for command in ['add text "buy milk"', 'add task "do work" --deadline 2026-01-01 12:00',
                        'add event x --start-time "2026-01-01 12:00" --alarm 2026-01-01',
                        'add contact --name A --address B --mobile +852', 'edit 1 --text x',
                        'print', 'print ALL', 'print 1', 'delete 1', 'save', 'save "my file.pim"',
                        'load a.pim', 'help', 'exit', 'quit', 'search \'text contains "buy milk"\'']:
            with self.subTest(command=command):
                self.assertIsInstance(parser.parse(command), Command)
        self.assertEqual(parser.parse('quit').name, 'exit')

    def test_invalid_commands(self):
        """Missing/extra/duplicate/unknown arguments and invalid IDs fail in the parser."""
        commands = ['', None, 'unknown', 'help x', 'exit x', 'delete', 'load', 'delete abc',
                    'print -1', 'print 0', 'delete ²', 'print 1 2', 'save ""', 'search',
                    'search "bad', 'add text "bad', 'edit', 'edit 1', 'edit 1 stray',
                    'add', 'add unknown x', 'add text', 'add text --text x', 'add text a b',
                    'add text x --text y', 'add task x', 'add contact --name x --name y',
                    'add text x --deadline 2026-01-01', 'edit 1 --unknown x', 'edit 1 --text',
                    'edit 1 --text --name x', 'edit 1 --start x --start_time y', 'x' * 16385,
                    'print ' + '9' * 101]
        for command in commands:
            with self.subTest(command=command), self.assertRaises(InvalidCommandError):
                CommandParser().parse(command)


class StorageContractTests(unittest.TestCase):
    def test_path_inspection_failure_is_a_domain_error(self):
        """An OS failure while inspecting a path must not escape as an unhandled error."""
        for operation in [lambda: Storage.save('unreadable.pim', PIMManager()),
                          lambda: Storage.load('unreadable.pim')]:
            with patch('pathlib.Path.is_symlink', side_effect=OSError('path too long')):
                with self.assertRaises(StorageError):
                    operation()

    def test_cleanup_failure_is_reported_without_corrupting_target(self):
        """A failed temporary-file cleanup reports its path and preserves the saved data."""
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'records.pim'
            Storage.save(path, PIMManager(records()))
            before = path.read_bytes()
            with patch('storage.storage.os.replace', side_effect=OSError('disk failure')):
                with patch('pathlib.Path.unlink', side_effect=OSError('cleanup denied')):
                    with self.assertRaises(StorageError) as caught:
                        Storage.save(path, PIMManager())
            self.assertIn('cleanup denied', str(caught.exception))
            self.assertEqual(path.read_bytes(), before)

    def test_all_types_and_empty_collection_roundtrip(self):
        """US10/11: all fields, Unicode and next_id survive disk round-trips."""
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'records.pim'
            for manager in [PIMManager(), PIMManager(records(), 10)]:
                Storage.save(path, manager)
                self.assertEqual(Storage.load(path).to_dict(), manager.to_dict())

    def test_invalid_files_and_extensions(self):
        """Bad JSON, encoding, schema, duplicate keys and wrong paths yield StorageError."""
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'bad.pim'
            for payload in [b'not JSON', b'\xff', b'{}', b'{"pirs": [], "pirs": []}',
                            b'{"schema_version": NaN}', b'[' * 2000,
                            json.dumps({'schema_version': 1, 'next_id': 2, 'pirs': [{'id': 1, 'type': None}]}).encode()]:
                path.write_bytes(payload)
                with self.assertRaises(StorageError):
                    Storage.load(path)
            with self.assertRaises(StorageError):
                Storage.load(Path(folder) / 'missing.pim')
            with self.assertRaises(StorageError):
                Storage.save(Path(folder) / 'missing' / 'x.pim', PIMManager())
            for name in ['', None, 'bad.txt', 'bad\x00.pim']:
                with self.assertRaises(StorageError):
                    pim_path(name)
            link = Path(folder) / 'link.pim'
            link.symlink_to(path)
            with self.assertRaises(StorageError):
                Storage.load(link)

    def test_failure_does_not_truncate_existing_file(self):
        """If replacement fails, old bytes remain and the temporary file is removed."""
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'records.pim'
            Storage.save(path, PIMManager(records()))
            before = path.read_bytes()
            with patch('storage.storage.os.replace', side_effect=OSError('disk failure')), self.assertRaises(StorageError):
                Storage.save(path, PIMManager())
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual(sorted(p.name for p in Path(folder).iterdir()), ['records.pim'])

    def test_size_limits_and_serialization_failure(self):
        """Oversized files and invalid UTF-8 data cannot corrupt a saved collection."""
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'records.pim'
            with patch('storage.storage.MAX_FILE_BYTES', 1), self.assertRaises(StorageError):
                Storage.save(path, PIMManager())
            self.assertFalse(path.exists())
            path.write_text('{}')
            with patch('storage.storage.MAX_FILE_BYTES', 1), self.assertRaises(StorageError):
                Storage.load(path)
            manager = PIMManager()
            manager.add_pir(TextPIR(text='\ud800'))
            with self.assertRaises(StorageError):
                Storage.save(path, manager)
            self.assertEqual(path.read_text(), '{}')


class ReplContractTests(unittest.TestCase):
    def test_overwrite_inspection_failure_is_a_domain_error(self):
        """Filesystem errors during overwrite confirmation preserve active state."""
        repl = Repl()
        repl.manager.add_pir(TextPIR(text='keep me'))
        repl.dirty = True
        with patch('pathlib.Path.exists', side_effect=OSError('permission denied')):
            with self.assertRaises(StorageError):
                repl.execute(Command('save', ['unreadable.pim']))
        self.assertTrue(repl.dirty)
        self.assertEqual(repl.manager.get_pir(1).get_text(), 'keep me')

    def test_full_workflow_and_confirmation(self):
        """US1-11: execute every CLI operation and require approval before overwriting state."""
        with tempfile.TemporaryDirectory() as folder, contextlib.redirect_stdout(io.StringIO()) as output:
            path = Path(folder) / 'demo.pim'
            repl = Repl(confirm=lambda _: True)
            for command in ['help', 'add text "buy milk"', 'add task report --deadline 2026-11-19 20:00',
                            'add event meeting --start 2026-10-12 09:00 --alarm 2026-10-12 08:30',
                            'add contact --name Alice --address "Hong Kong" --mobile 61234567',
                            'edit 1 --text "buy coffee"', 'search type = task && deadline < 2027-01-01',
                            'print all', 'print 1', f'save "{path}"', 'delete 4', f'load "{path}"']:
                self.assertFalse(repl.execute(repl.parser.parse(command)))
            self.assertEqual(len(repl.manager.pirs), 4)
            self.assertFalse(repl.dirty)
            self.assertTrue(repl.execute(Command('exit')))
            self.assertIn('buy coffee', output.getvalue())

    def test_cancelled_save_load_exit_keep_state(self):
        """Declining confirmation preserves file bytes, active model and dirty flag."""
        with tempfile.TemporaryDirectory() as folder, contextlib.redirect_stdout(io.StringIO()):
            path = Path(folder) / 'records.pim'
            Storage.save(path, PIMManager(records()))
            before = path.read_bytes()
            repl = Repl(confirm=lambda _: False)
            repl.execute(repl.parser.parse('add text new'))
            for command in [f'save "{path}"', f'load "{path}"', 'exit']:
                self.assertFalse(repl.execute(repl.parser.parse(command)))
                self.assertEqual(repl.manager.get_pir(1).get_text(), 'new')
                self.assertTrue(repl.dirty)
                self.assertEqual(path.read_bytes(), before)

    def test_bad_load_keeps_active_model(self):
        """Load failure must leave the current manager unchanged without asking confirmation."""
        repl = Repl(confirm=lambda _: self.fail('must validate before confirmation'))
        repl.manager.add_pir(TextPIR(text='keep me'))
        repl.dirty = True
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'bad.pim'
            path.write_text('{}')
            with self.assertRaises(StorageError):
                repl.execute(Command('load', [str(path)]))
        self.assertEqual(repl.manager.get_pir(1).get_text(), 'keep me')

    def test_confirmation_input_and_eof(self):
        """Only explicit yes approves a destructive replacement; EOF/Ctrl-C cancel."""
        repl = Repl()
        for answer, expected in [('y', True), ('YES', True), ('', False), ('n', False)]:
            with patch('builtins.input', return_value=answer):
                self.assertEqual(repl._confirm('test'), expected)
        for error in [EOFError, KeyboardInterrupt]:
            with patch('builtins.input', side_effect=error):
                self.assertFalse(repl._confirm('test'))

    def test_loop_eof_interrupt_and_domain_errors(self):
        """Input cancellation and bad commands preserve the loop, with EOF warning if dirty."""
        repl = Repl()
        with patch('builtins.input', side_effect=['', KeyboardInterrupt, 'delete 99', 'add text x', EOFError]), contextlib.redirect_stdout(io.StringIO()) as output:
            repl.run()
        self.assertIn('Input cancelled', output.getvalue())
        self.assertIn('Error:', output.getvalue())
        self.assertIn('unsaved', output.getvalue())
        with patch('builtins.input', side_effect=EOFError), contextlib.redirect_stdout(io.StringIO()):
            Repl().run()

    def test_empty_output_and_unknown_command(self):
        """Empty result sets are explained, and invalid dispatch raises a domain error."""
        with contextlib.redirect_stdout(io.StringIO()) as output:
            Printer().print_all([])
        self.assertIn('No matching PIRs', output.getvalue())
        with self.assertRaises(InvalidCommandError):
            Repl().execute(Command('bad'))
