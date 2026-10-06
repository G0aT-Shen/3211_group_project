"""Independent process acceptance and architecture checks beyond model unit tests."""
import ast
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class AcceptanceTests(unittest.TestCase):
    def test_real_process_all_user_stories(self):
        """US1-11: exact fields survive CLI operations, disk storage and a new process."""
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'session.pim'
            all_types = Path(folder) / 'all_types.pim'
            restored = Path(folder) / 'restored.pim'
            commands = [
                'print abc', 'delete', 'delete abc', 'add text "buy milk"',
                'add task report --deadline 2026-11-19 20:00',
                'add event meeting --start 2026-10-12 09:00 --alarm 2026-10-12 08:30',
                'add contact --name Alice --address "Hong Kong" --mobile 01234567',
                'search text contains "buy milk"', 'edit 1 --text "buy coffee"',
                'edit 2 --deadline 2026-11-20 12:00',
                'search (type = task || type = event) && !description contains "missing"',
                'print all', 'print 4', f'save "{all_types}"',
                'delete 2', f'save "{path}"', f'load "{path}"',
                'add text afterload', f'save "{path}"', 'y', 'exit',
            ]
            result = subprocess.run([sys.executable, str(ROOT / 'main.py')], input='\n'.join(commands) + '\n',
                                    text=True, capture_output=True, cwd=folder, timeout=15)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stderr, '')
            self.assertEqual(result.stdout.count('Error:'), 3)
            self.assertIn('buy coffee', result.stdout)
            self.assertIn('Created PIR #5', result.stdout)
            expected_records = [
                {'id': 1, 'type': 'text', 'text': 'buy coffee'},
                {'id': 2, 'type': 'task', 'description': 'report',
                 'deadline': '2026-11-20T12:00:00'},
                {'id': 3, 'type': 'event', 'description': 'meeting',
                 'start_time': '2026-10-12T09:00:00', 'alarm': '2026-10-12T08:30:00'},
                {'id': 4, 'type': 'contact', 'name': 'Alice',
                 'address': 'Hong Kong', 'mobile': '01234567'},
            ]
            self.assertEqual(json.loads(all_types.read_text(encoding='utf-8')),
                             {'schema_version': 1, 'next_id': 5, 'pirs': expected_records})
            self.assertEqual(json.loads(path.read_text(encoding='utf-8')),
                             {'schema_version': 1, 'next_id': 6,
                              'pirs': [expected_records[i] for i in (0, 2, 3)] +
                                      [{'id': 5, 'type': 'text', 'text': 'afterload'}]})

            second_commands = [f'load "{all_types}"', 'print all',
                               'add text "after restart"', f'save "{restored}"', 'exit']
            second = subprocess.run([sys.executable, str(ROOT / 'main.py')],
                                    input='\n'.join(second_commands) + '\n',
                                    text=True, capture_output=True, cwd=folder, timeout=15)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual(second.stderr, '')
            self.assertNotIn('Error:', second.stdout)
            for line in ['#1 [text] buy coffee',
                         '#2 [task] report (deadline: 2026-11-20 12:00)',
                         '#3 [event] meeting (start: 2026-10-12 09:00, alarm: 2026-10-12 08:30)',
                         '#4 [contact] Alice (address: Hong Kong, mobile: 01234567)']:
                self.assertIn(line, second.stdout)
            self.assertEqual(json.loads(restored.read_text(encoding='utf-8')),
                             {'schema_version': 1, 'next_id': 6,
                              'pirs': expected_records +
                                      [{'id': 5, 'type': 'text', 'text': 'after restart'}]})

    def test_model_has_no_io_or_outer_layer_imports(self):
        """The model stays independently testable without importing CLI, storage or view."""
        forbidden = {'cli', 'controller', 'storage', 'view'}
        for source in (ROOT / 'model').glob('*.py'):
            for node in ast.walk(ast.parse(source.read_text(encoding='utf-8'))):
                if isinstance(node, ast.Import):
                    self.assertFalse({a.name.split('.')[0] for a in node.names} & forbidden, source.name)
                if isinstance(node, ast.ImportFrom) and node.level == 0:
                    self.assertNotIn((node.module or '').split('.')[0], forbidden, source.name)
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    self.assertNotIn(node.func.id, {'open', 'print', 'input'}, source.name)

    def test_production_imports_are_standard_library_or_project(self):
        """All production imports come from the explicit stdlib/project allowlist."""
        allowed = {'__future__', 'abc', 'datetime', 're', 'typing', 'types', 'operator', 'shlex',
                   'dataclasses', 'json', 'os', 'pathlib', 'stat', 'sys', 'tempfile', 'model', 'controller', 'cli', 'storage', 'view'}
        files = [ROOT / 'main.py']
        for package in ['model', 'controller', 'cli', 'storage', 'view']:
            files.extend((ROOT / package).glob('*.py'))
        for source in files:
            for node in ast.walk(ast.parse(source.read_text(encoding='utf-8'))):
                if isinstance(node, ast.Import):
                    self.assertTrue({a.name.split('.')[0] for a in node.names} <= allowed, source.name)
                if isinstance(node, ast.ImportFrom) and node.level == 0:
                    self.assertIn(node.module.split('.')[0], allowed, source.name)
