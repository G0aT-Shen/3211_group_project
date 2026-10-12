"""Process-level regressions for console encoding and retained session data."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ConsoleEncodingTests(unittest.TestCase):
    def test_unicode_output_preserves_session_with_limited_or_utf8_encoding(self):
        """Unsupported output characters cannot prevent later commands or saving."""
        text = '\u4f60\u597d \U0001f600'
        snapshot = {'schema_version': 1, 'next_id': 2,
                    'pirs': [{'id': 1, 'type': 'text', 'text': text}]}
        commands = 'load records.pim\nadd text unsaved\nprint all\nsave kept.pim\nexit\n'
        for encoding in ('ascii', 'cp1252', 'cp936', 'utf-8'):
            with self.subTest(encoding=encoding), tempfile.TemporaryDirectory() as folder:
                path = Path(folder)
                (path / 'records.pim').write_text(json.dumps(snapshot), encoding='utf-8')
                result = subprocess.run(
                    [sys.executable, str(ROOT / 'main.py')],
                    input=commands, text=True, encoding=encoding, capture_output=True,
                    cwd=folder, timeout=10,
                    env=dict(os.environ, PYTHONIOENCODING=f'{encoding}:strict'))
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stderr, '')
                rendered = text.encode(encoding, errors='backslashreplace').decode(encoding)
                self.assertIn(f'#1 [text] {rendered}', result.stdout)
                self.assertIn('#2 [text] unsaved', result.stdout)
                self.assertIn('Goodbye.', result.stdout)
                saved = json.loads((path / 'kept.pim').read_text(encoding='utf-8'))
                self.assertEqual(saved['pirs'][0], snapshot['pirs'][0])
                self.assertEqual(saved['pirs'][1]['text'], 'unsaved')
                self.assertEqual(saved['next_id'], 3)

    def test_undecodable_input_is_rejected_without_losing_session(self):
        """Undecodable input bytes produce an error, not a traceback; unsaved records survive."""
        # \xe9 and \xff are invalid in both encodings. The \xff line answers the exit
        # prompt, which must cancel the exit instead of discarding the unsaved record.
        commands = b'add text kept\nadd text "caf\xe9"\nexit\n\xff\nprint all\nsave kept.pim\nexit\n'
        for encoding in ('ascii', 'utf-8'):
            with self.subTest(encoding=encoding), tempfile.TemporaryDirectory() as folder:
                result = subprocess.run(
                    [sys.executable, str(ROOT / 'main.py')],
                    input=commands, capture_output=True, cwd=folder, timeout=10,
                    env=dict(os.environ, PYTHONIOENCODING=f'{encoding}:strict'))
                self.assertEqual(result.returncode, 0, result.stderr.decode(errors='replace'))
                self.assertEqual(result.stderr, b'')
                output = result.stdout.decode(encoding)
                self.assertIn('Error: Text content must be valid UTF-8 text', output)
                self.assertIn('Exit cancelled.', output)
                self.assertIn('#1 [text] kept', output)
                self.assertIn('Goodbye.', output)
                saved = json.loads((Path(folder) / 'kept.pim').read_text(encoding='utf-8'))
                self.assertEqual(saved['pirs'], [{'id': 1, 'type': 'text', 'text': 'kept'}])
                self.assertEqual(saved['next_id'], 2)
