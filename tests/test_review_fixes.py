"""Regression tests for the full code review's runtime boundary defects."""
import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from cli import CommandParser, Repl
from model import PIMManager, PIRFactory, TextPIR, ValidationError
from storage import Storage

ROOT = Path(__file__).resolve().parents[1]
MAX_ID = 10 ** 100 - 1


class InterruptTests(unittest.TestCase):
    def test_interrupt_after_save_commit_keeps_exit_confirmation(self):
        """An interrupt after replace/dirty reset must not silently discard a session."""
        repl = Repl()
        print_msg = repl.printer.print_msg

        def interrupt_saved_message(message):
            if message.startswith('Saved to '):
                raise KeyboardInterrupt
            print_msg(message)

        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'committed.pim'
            commands = ['add text keep', f'save "{path}"', 'print all', 'exit', 'n']
            with patch('builtins.input', side_effect=commands + [EOFError]), \
                    patch.object(repl.printer, 'print_msg', side_effect=interrupt_saved_message), \
                    contextlib.redirect_stdout(io.StringIO()) as output:
                repl.run()
            self.assertEqual(Storage.load(path).get_pir(1).get_text(), 'keep')
            self.assertTrue(repl.dirty)
            self.assertIn('Exit cancelled', output.getvalue())

    def test_interrupting_read_only_command_does_not_mark_data_dirty(self):
        """Cancelling output keeps a clean collection clean and the prompt usable."""
        repl = Repl()
        with patch('builtins.input', side_effect=['print all', 'exit']), \
                patch.object(repl.printer, 'print_all', side_effect=KeyboardInterrupt), \
                contextlib.redirect_stdout(io.StringIO()) as output:
            repl.run()
        self.assertFalse(repl.dirty)
        self.assertIn('Goodbye.', output.getvalue())

    def test_interrupted_id_allocation_rolls_back_record_and_counter(self):
        """Cancelling a mutation cannot leave a record paired with a reusable ID."""
        class InterruptedInsert(dict):
            interrupted = False

            def __setitem__(self, key, value):
                super().__setitem__(key, value)
                if not self.interrupted:
                    self.interrupted = True
                    raise KeyboardInterrupt

        manager = PIMManager()
        # Fault injection models Ctrl-C just after the mapping mutation.
        manager._pirs = InterruptedInsert(manager.pirs)
        before = manager.to_dict()
        with self.assertRaises(KeyboardInterrupt):
            manager.add_pir(TextPIR(text='cancelled'))
        self.assertEqual(manager.to_dict(), before)
        record = manager.add_pir(TextPIR(text='next'))
        self.assertEqual(record.get_id(), 1)
        self.assertEqual(manager.next_id, 2)

    def test_interrupted_save_preserves_session_file_and_cleans_temp(self):
        """Ctrl-C during fsync keeps unsaved edits available for the next command."""
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'records.pim'
            original = PIMManager()
            original.add_pir(TextPIR(text='saved original'))
            Storage.save(path, original)
            before = path.read_bytes()
            repl = Repl(confirm=lambda _: True)
            output = io.StringIO()
            commands = ['add text unsaved', f'save "{path}"', 'print all']
            with patch('builtins.input', side_effect=commands + [EOFError]), \
                    patch('storage.storage.os.fsync', side_effect=KeyboardInterrupt), \
                    contextlib.redirect_stdout(output):
                try:
                    repl.run()
                except KeyboardInterrupt:
                    self.fail('Save interruption escaped the REPL')
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual(list(Path(folder).glob('.pim-*.tmp')), [])
            self.assertEqual(repl.manager.get_pir(1).get_text(), 'unsaved')
            self.assertTrue(repl.dirty)
            self.assertIn('#1 [text] unsaved', output.getvalue())
            self.assertIn('Command cancelled', output.getvalue())
            # A subsequent save still commits the retained records normally.
            with contextlib.redirect_stdout(io.StringIO()):
                repl.execute(repl.parser.parse(f'save "{path}"'))
            self.assertFalse(repl.dirty)
            self.assertEqual(Storage.load(path).to_dict(), repl.manager.to_dict())

    def test_interrupted_load_does_not_replace_active_records(self):
        """Ctrl-C during reading keeps the manager and permits subsequent commands."""
        repl = Repl()
        manager = repl.manager
        commands = ['add text keep', 'load interrupted.pim', 'print all', 'exit', 'n']
        with patch('builtins.input', side_effect=commands + [EOFError]), \
                patch.object(repl.storage, 'load', side_effect=KeyboardInterrupt), \
                contextlib.redirect_stdout(io.StringIO()) as output:
            try:
                repl.run()
            except KeyboardInterrupt:
                self.fail('Load interruption escaped the REPL')
        self.assertIs(repl.manager, manager)
        self.assertTrue(repl.dirty)
        self.assertIn('#1 [text] keep', output.getvalue())
        self.assertIn('Exit cancelled', output.getvalue())


class IDBoundaryTests(unittest.TestCase):
    def test_oversized_record_ids_are_rejected_at_every_model_boundary(self):
        """Records beyond CLI reach cannot be constructed, restored or looked up."""
        data = {'id': MAX_ID + 1, 'type': 'text', 'text': 'unreachable'}
        for operation in [lambda: TextPIR(MAX_ID + 1, 'unreachable'),
                          lambda: PIRFactory.from_dict(data),
                          lambda: PIMManager().get_pir(MAX_ID + 1)]:
            with self.subTest(operation=operation), self.assertRaises(ValidationError):
                operation()

    def test_next_id_cannot_exceed_the_exhausted_sentinel(self):
        """Malformed next_id values fail in constructors and file restoration."""
        data = {'schema_version': 1, 'next_id': MAX_ID + 2, 'pirs': []}
        for operation in [lambda: PIMManager(next_id=MAX_ID + 2),
                          lambda: PIMManager.from_dict(data)]:
            with self.subTest(operation=operation), self.assertRaises(ValidationError):
                operation()

    def test_last_id_remains_usable_and_exhaustion_survives_save_load(self):
        """The final addressable ID works; exhaustion never reuses an ID or corrupts a file."""
        repl = Repl(PIMManager(next_id=MAX_ID), confirm=lambda _: True)
        with tempfile.TemporaryDirectory() as folder, contextlib.redirect_stdout(io.StringIO()):
            path = Path(folder) / 'last.pim'
            repl.execute(CommandParser().parse('add text last'))
            self.assertEqual(repl.manager.next_id, MAX_ID + 1)
            repl.execute(CommandParser().parse(f'print {MAX_ID}'))
            repl.execute(CommandParser().parse(f'edit {MAX_ID} --text updated'))
            snapshot = repl.manager.to_dict()
            with self.assertRaisesRegex(ValidationError, 'exhausted'):
                repl.manager.add_pir(TextPIR(text='overflow'))
            self.assertEqual(repl.manager.to_dict(), snapshot)
            repl.execute(CommandParser().parse(f'save "{path}"'))
            repl.execute(CommandParser().parse(f'load "{path}"'))
            self.assertEqual(repl.manager.to_dict(), snapshot)
            repl.execute(CommandParser().parse(f'delete {MAX_ID}'))
            Storage.save(path, repl.manager)
            restored = Storage.load(path)
            self.assertEqual(restored.next_id, MAX_ID + 1)
            with self.assertRaisesRegex(ValidationError, 'exhausted'):
                restored.add_pir(TextPIR(text='no reuse'))

    def test_exhausted_file_cannot_create_an_unaddressable_record(self):
        """The original oversized-next_id reproduction leaves the CLI usable."""
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'exhausted.pim'
            path.write_text(json.dumps({'schema_version': 1, 'next_id': MAX_ID + 1, 'pirs': []}))
            result = subprocess.run([sys.executable, '-X', 'utf8', str(ROOT / 'main.py')],
                                    input=f'load "{path}"\nadd text unreachable\nprint all\nexit\n',
                                    text=True, encoding='utf-8', capture_output=True, timeout=5)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stderr, '')
            self.assertIn('exhausted', result.stdout)
            self.assertNotIn('Created PIR', result.stdout)
            self.assertIn('No matching PIRs.', result.stdout)


class RegularFileTests(unittest.TestCase):
    @unittest.skipUnless(hasattr(os, 'mkfifo'), 'Named pipes require POSIX')
    def test_fifo_load_is_rejected_without_blocking_or_losing_records(self):
        """A real FIFO produces a domain error, then the same process can save."""
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            fifo = folder / 'blocked.pim'
            os.mkfifo(fifo)
            saved = folder / 'kept.pim'
            commands = f'add text keep\nload "{fifo}"\nprint all\nsave "{saved}"\nexit\n'
            result = subprocess.run([sys.executable, '-X', 'utf8', str(ROOT / 'main.py')], input=commands,
                                    text=True, encoding='utf-8', capture_output=True, timeout=3)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stderr, '')
            self.assertIn('regular file', result.stdout)
            self.assertIn('#1 [text] keep', result.stdout)
            self.assertEqual(Storage.load(saved).get_pir(1).get_text(), 'keep')
