"""Windows path contracts plus real UTF-8/CRLF process portability checks."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from cli import CommandParser
from model.exceptions import StorageError
from storage.storage import pim_path

ROOT = Path(__file__).resolve().parents[1]


class WindowsPathTests(unittest.TestCase):
    def test_device_names_are_rejected_before_filesystem_access(self):
        """CON and friends must never reach an opener that can wait for device input."""
        names = ['CON.pim', 'prn.PIM', 'AUX.pim', 'NUL.pim', 'CON .pim',
                 'CONIN$.pim', 'CONOUT$.pim', 'COM1.pim', 'COM9.pim',
                 'LPT1.pim', 'LPT9.pim', 'COM¹.pim', 'LPT².pim', 'COM³.pim',
                 r'C:\review\NUL\records.pim', r'\\server\share\AUX\records.pim']
        with patch('storage.storage.WINDOWS', True, create=True):
            for name in names:
                with self.subTest(path=name), patch.object(Path, 'is_symlink', return_value=False) as inspected:
                    with self.assertRaisesRegex(StorageError, 'Windows'):
                        pim_path(name)
                    inspected.assert_not_called()

    def test_streams_invalid_components_and_device_namespaces_are_rejected(self):
        """A Windows filename must refer to an ordinary file without path aliasing."""
        names = ['records.pim:stream.pim', 'bad?.pim', 'bad*.pim', 'bad|.pim',
                 'bad<.pim', 'bad>.pim', 'bad".pim', 'bad\x01.pim',
                 r'C:\review.\records.pim', r'C:\review \records.pim',
                 r'C:\records.pim \other.pim', r'\\.\C:\records.pim',
                 r'\\?\C:\records.pim']
        with patch('storage.storage.WINDOWS', True, create=True):
            for name in names:
                with self.subTest(path=repr(name)), patch.object(Path, 'is_symlink', return_value=False) as inspected:
                    with self.assertRaisesRegex(StorageError, 'Windows'):
                        pim_path(name)
                    inspected.assert_not_called()

    def test_normal_drive_unc_unicode_and_posix_style_paths_are_preserved(self):
        """Spaces, Unicode, drive letters and network shares remain valid Windows paths."""
        names = ['records.PIM', 'CONsole.pim', 'COM10.pim', 'LPT0.pim',
                 r'C:\教授检阅\my records.pim', r'\\server\share\my records.pim',
                 'C:/review folder/records.pim', '\u00a0records.pim']
        with patch('storage.storage.WINDOWS', True, create=True), \
                patch.object(Path, 'is_symlink', return_value=False):
            for name in names:
                with self.subTest(path=name):
                    self.assertEqual(pim_path(name), Path(name))

    def test_single_quoted_windows_paths_survive_command_parsing(self):
        """The documented quoting works identically for drive and UNC paths on either OS."""
        names = [r'C:\教授检阅\my records.pim', r'\\server\share\my records.pim',
                 'C:/review folder/records.pim']
        for name in names:
            for command in ['save', 'load']:
                with self.subTest(command=command, path=name):
                    self.assertEqual(CommandParser().parse(f"{command} '{name}'").args, [name])


class PortableProcessTests(unittest.TestCase):
    def test_unicode_directory_crlf_commands_and_files_roundtrip(self):
        """A copied project runs from a different directory and preserves portable UTF-8 files."""
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            project = root / '教授检阅 project'
            project.mkdir()
            shutil.copyfile(ROOT / 'main.py', project / 'main.py')
            for package in ['model', 'controller', 'cli', 'storage', 'view']:
                shutil.copytree(ROOT / package, project / package,
                                ignore=shutil.ignore_patterns('__pycache__'))
            data = root / '中文 data'
            data.mkdir()
            path = data / 'my records.PIM'
            expected = {'schema_version': 1, 'next_id': 5, 'pirs': [
                {'id': 1, 'type': 'text', 'text': '你好 😀'},
                {'id': 2, 'type': 'task', 'description': '报告', 'deadline': '2026-11-20T12:00:00'},
                {'id': 3, 'type': 'event', 'description': '会议',
                 'start_time': '2026-10-12T09:00:00', 'alarm': '2026-10-12T08:30:00'},
                {'id': 4, 'type': 'contact', 'name': '李明', 'address': '香港', 'mobile': '01234567'},
            ]}
            commands = ['add text "你好 😀"', 'add task "报告" --deadline 2026-11-20 12:00',
                        'add event "会议" --start 2026-10-12 09:00 --alarm 2026-10-12 08:30',
                        'add contact --name "李明" --address "香港" --mobile 01234567',
                        f"save '{path}'", 'exit']
            for phase in ['save', 'load']:
                if phase == 'load':
                    # A file with Windows line endings must load on both operating systems.
                    path.write_bytes(path.read_bytes().replace(b'\n', b'\r\n'))
                    commands = [f"load '{path}'", 'search text = "你好 😀"',
                                'add text "after restart"', f"save '{path}'", 'y', 'exit']
                    expected['pirs'].append({'id': 5, 'type': 'text', 'text': 'after restart'})
                    expected['next_id'] = 6
                result = subprocess.run(
                    [sys.executable, '-X', 'utf8', str(project / 'main.py')],
                    input=('\r\n'.join(commands) + '\r\n').encode('utf-8'),
                    capture_output=True, cwd=root, timeout=15,
                    env=dict(os.environ, PYTHONIOENCODING='utf-8:strict'))
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stderr, b'')
                output = result.stdout.decode('utf-8')
                self.assertNotIn('Error:', output)
                self.assertIn('Goodbye.', output)
                if phase == 'load':
                    self.assertIn('#1 [text] 你好 😀', output)
                    self.assertIn('Created PIR #5', output)
                self.assertEqual(json.loads(path.read_text(encoding='utf-8')), expected)

    @unittest.skipUnless(os.name == 'nt', 'Requires the real Windows command interpreter')
    def test_windows_launcher_runs_from_another_working_directory(self):
        """CMD resolves a spaced project path, selects Python and enables UTF-8."""
        with tempfile.TemporaryDirectory() as folder:
            project = Path(folder) / '教授 review project'
            project.mkdir()
            shutil.copyfile(ROOT / 'run_windows.cmd', project / 'run_windows.cmd')
            shutil.copyfile(ROOT / 'main.py', project / 'main.py')
            for package in ['model', 'controller', 'cli', 'storage', 'view']:
                shutil.copytree(ROOT / package, project / package,
                                ignore=shutil.ignore_patterns('__pycache__'))
            result = subprocess.run(
                ['cmd.exe', '/d', '/c', str(project / 'run_windows.cmd')],
                input='add text "你好 😀"\nsave records.pim\nexit\n'.encode('utf-8'),
                capture_output=True, cwd=folder, timeout=15,
                env=dict(os.environ, PYTHONIOENCODING='ascii:strict'))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stderr, b'')
            self.assertIn('Goodbye.', result.stdout.decode('utf-8'))
            self.assertEqual(json.loads((project / 'records.pim').read_text(encoding='utf-8'))['pirs'],
                             [{'id': 1, 'type': 'text', 'text': '你好 😀'}])
