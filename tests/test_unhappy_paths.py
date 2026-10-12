"""Failure recovery contracts for the interactive application."""

import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from cli import Repl
from model import PIMManager, TextPIR
from storage import Storage


class UnhappyPathTests(unittest.TestCase):
    def test_repeated_bad_commands_preserve_state_and_allow_recovery(self):
        """Mistakes preserve records, IDs and the clean/dirty flag until a valid edit."""
        invalid = [
            'add text "unterminated', 'search "unterminated', 'search',
            'add task missing-deadline', 'add task bad-date --deadline 2026-02-30',
            'add text ""', 'add text "\ud800"',
            'edit 1 --text changed --typo x', 'edit 1 --text first --text second',
            'edit 1 --deadline 2026-01-01', 'edit 1 --text --name x',
            'delete 0', 'delete 999', 'print ' + '9' * 101,
            'search text contains x &&', 'search (type = text',
            'search text = x || unknown = y', 'search ' + '!' * 65 + 'type = text',
            'search ' + 'x' * 8193, 'x' * 16385,
        ]
        for initially_dirty in (False, True):
            with self.subTest(dirty=initially_dirty):
                repl = Repl(confirm=lambda _: True)
                repl.manager.add_pir(TextPIR(text='original'))
                repl.dirty = initially_dirty
                before = repl.manager.to_dict()

                def commands():
                    for command in invalid:
                        yield command
                        self.assertEqual(repl.manager.to_dict(), before, repr(command))
                        self.assertEqual(repl.dirty, initially_dirty, repr(command))
                    yield 'edit 1 --text recovered'
                    yield 'add text next'
                    yield 'exit'

                with patch('builtins.input', side_effect=commands()), \
                        contextlib.redirect_stdout(io.StringIO()) as output:
                    repl.run()
                self.assertEqual(output.getvalue().count('Error:'), len(invalid))
                self.assertIn('Goodbye.', output.getvalue())
                self.assertEqual(repl.manager.get_pir(1).get_text(), 'recovered')
                self.assertEqual(repl.manager.get_pir(2).get_text(), 'next')
                self.assertEqual(repl.manager.next_id, 3)
                self.assertTrue(repl.dirty)

    def test_save_failures_preserve_disk_and_session_then_allow_retry(self):
        """Creation, write, flush, sync and replacement failures never commit a partial save."""
        original_tempfile = tempfile.NamedTemporaryFile
        for stage in ('create', 'write', 'flush', 'sync', 'replace'):
            with self.subTest(stage=stage), tempfile.TemporaryDirectory() as folder:
                path = Path(folder) / 'records.pim'
                old = PIMManager()
                old.add_pir(TextPIR(text='on disk'))
                Storage.save(path, old)
                old_bytes = path.read_bytes()
                repl = Repl(confirm=lambda _: True)
                repl.manager.add_pir(TextPIR(text='unsaved'))
                repl.dirty = True
                before = repl.manager.to_dict()

                @contextlib.contextmanager
                def failing_stream(**kwargs):
                    with original_tempfile(**kwargs) as stream:
                        with patch.object(stream, stage, side_effect=OSError('disk full')):
                            yield stream

                if stage in ('write', 'flush'):
                    fault = patch('storage.storage.tempfile.NamedTemporaryFile', failing_stream)
                else:
                    target = {'create': 'tempfile.NamedTemporaryFile',
                              'sync': 'os.fsync', 'replace': 'os.replace'}[stage]
                    fault = patch('storage.storage.' + target, side_effect=OSError('disk unavailable'))
                with fault, patch('builtins.input', side_effect=[f'save "{path}"', 'print all', EOFError]), \
                        contextlib.redirect_stdout(io.StringIO()) as output:
                    repl.run()
                self.assertEqual(output.getvalue().count('Error:'), 1)
                self.assertIn('#1 [text] unsaved', output.getvalue())
                self.assertEqual(repl.manager.to_dict(), before)
                self.assertTrue(repl.dirty)
                self.assertEqual(path.read_bytes(), old_bytes)
                self.assertEqual(list(Path(folder).iterdir()), [path])
                with contextlib.redirect_stdout(io.StringIO()):
                    repl.execute(repl.parser.parse(f'save "{path}"'))
                self.assertFalse(repl.dirty)
                self.assertEqual(Storage.load(path).to_dict(), before)

    def test_bad_loads_preserve_session_and_do_not_request_discard(self):
        """Broken files cannot replace active data, even after some records were decoded."""
        good_record = {'id': 1, 'type': 'text', 'text': 'from file'}
        invalid_payloads = [
            b'{', b'\xff', b'{"schema_version":1,"schema_version":1,"next_id":1,"pirs":[]}',
            b'{"schema_version":1,"next_id":NaN,"pirs":[]}',
            json.dumps({'schema_version': 1, 'next_id': 3,
                        'pirs': [good_record, {'id': 2, 'type': 'task', 'description': 'missing date'}]}).encode(),
            json.dumps({'schema_version': 1, 'next_id': 3, 'pirs': [good_record, good_record]}).encode(),
            json.dumps({'schema_version': 1, 'next_id': 1, 'pirs': [good_record]}).encode(),
        ]
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'broken.pim'
            repl = Repl(confirm=lambda _: self.fail('failed loads must not ask to discard data'))
            repl.manager.add_pir(TextPIR(text='keep me'))
            repl.dirty = True
            manager = repl.manager
            before = manager.to_dict()

            def commands():
                # Start with a missing file, then try the malformed files.
                for payload in [None] + invalid_payloads:
                    if payload is not None:
                        path.write_bytes(payload)
                    yield f'load "{path}"'
                    self.assertIs(repl.manager, manager)
                    self.assertEqual(manager.to_dict(), before)
                    self.assertTrue(repl.dirty)
                yield 'print all'
                raise EOFError

            with patch('builtins.input', side_effect=commands()), \
                    contextlib.redirect_stdout(io.StringIO()) as output:
                repl.run()
            self.assertEqual(output.getvalue().count('Error:'), len(invalid_payloads) + 1)
            self.assertIn('#1 [text] keep me', output.getvalue())


if __name__ == '__main__':
    unittest.main()
