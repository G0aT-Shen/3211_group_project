"""Failure contracts for recording a real CLI demonstration."""
import importlib.util
import os
from pathlib import Path
import unittest
from unittest.mock import patch


@unittest.skipUnless(os.name == 'posix', 'PTY recording requires POSIX')
class DemoCaptureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location(
            'demo_session', Path(__file__).resolve().parents[1] / 'tools/demo_session.py')
        cls.recorder = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.recorder)

    def test_startup_failure_closes_both_pty_descriptors(self):
        """An unavailable child process cannot leak either terminal descriptor."""
        descriptors = self.recorder.pty.openpty()
        try:
            with patch.object(self.recorder.pty, 'openpty', return_value=descriptors), \
                    patch.object(self.recorder.subprocess, 'Popen', side_effect=OSError('cannot start child')):
                with self.assertRaisesRegex(OSError, 'cannot start child'):
                    self.recorder.capture()
            for descriptor in descriptors:
                with self.assertRaises(OSError):
                    os.fstat(descriptor)
        finally:
            for descriptor in descriptors:
                try:
                    os.close(descriptor)
                except OSError:
                    pass

    def test_early_child_exit_cannot_look_like_a_successful_prompt(self):
        """EOF before the required prompt is a recording failure, even after partial output."""
        with patch.object(self.recorder.select, 'select', return_value=([1], [], [])), \
                patch.object(self.recorder.os, 'read', side_effect=[b'partial output', b'']):
            with self.assertRaisesRegex(RuntimeError, 'expected prompt'):
                self.recorder.read_until(1, 'pim> ')

    def test_prompt_and_expected_exit_preserve_output(self):
        """Normal prompts and EOF after exit keep the captured terminal text unchanged."""
        for marker, chunks, expected in (
                ('pim> ', [b'hello\r\n', b'pim> '], 'hello\npim> '),
                (None, [b'Goodbye.\r\n', b''], 'Goodbye.\n')):
            with self.subTest(marker=marker), \
                    patch.object(self.recorder.select, 'select', return_value=([1], [], [])), \
                    patch.object(self.recorder.os, 'read', side_effect=chunks):
                self.assertEqual(self.recorder.read_until(1, marker), expected)
