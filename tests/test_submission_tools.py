"""Release-gate regression checks protect against incomplete final packaging."""
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location('submission_check', Path(__file__).resolve().parents[1] / 'tools/check_submission.py')
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)
_COVERAGE_SPEC = importlib.util.spec_from_file_location(
    'coverage_check', Path(__file__).resolve().parents[1] / 'tools/check_coverage.py')
coverage_checker = importlib.util.module_from_spec(_COVERAGE_SPEC)
_COVERAGE_SPEC.loader.exec_module(coverage_checker)


def mp4(seconds):
    body = b'\0' * 12 + struct.pack('>II', 1000, seconds * 1000)
    header = struct.pack('>I4s', len(body) + 8, b'mvhd') + body
    return struct.pack('>I4s', len(header) + 8, b'moov') + header


class SubmissionTests(unittest.TestCase):
    def test_coverage_counts_unreported_source_as_missed(self):
        """A trace version that omits a .cover file must not crash the report."""
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / '__init__.py'
            source.write_text('VALUE = 1\n', encoding='utf-8')
            covered, total = coverage_checker.coverage_counts(
                source, Path(folder) / 'missing.cover')
            self.assertEqual(covered, 0)
            self.assertGreater(total, 0)

    def test_missing_files_and_pending_human_approvals_fail(self):
        """An empty submission never passes merely because code tests passed."""
        with tempfile.TemporaryDirectory() as folder:
            issues = checker.check(Path(folder))
            self.assertTrue(any('Honour Declaration' in issue for issue in issues))
            self.assertTrue(any('Human review pending' in issue for issue in issues))

    def test_complete_gate_and_duration_checks(self):
        """All files plus explicit review are required; overlong video is rejected."""
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for name in checker.REQUIRED:
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b'%PDF-test' if path.suffix == '.pdf' else b'test')
            (root/'output/demo/system_demo.mp4').write_bytes(mp4(124))
            (root/'submission_inputs/presentation_recording.mp4').write_bytes(mp4(280))
            status = root/'submission_inputs/review_status.json'
            status.write_text(json.dumps(dict.fromkeys(checker.APPROVALS, True)))
            self.assertEqual(checker.check(root), [])
            (root/'output/demo/system_demo.mp4').write_bytes(mp4(241))
            self.assertTrue(any('excessive duration' in issue for issue in checker.check(root)))
            status.write_text('[]')
            self.assertTrue(any('Invalid review status' in issue for issue in checker.check(root)))

    def test_malformed_video_and_unresolved_placeholders(self):
        """An invalid MP4 header is rejected and unresolved team markers remain visible."""
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path = root/'x.mp4'
            for content in [b'', b'not a video', struct.pack('>I4s', 9999, b'moov')]:
                path.write_bytes(content)
                self.assertIsNone(checker.mp4_duration(path))
            source = root/'docs/SRS.md'
            source.parent.mkdir()
            source.write_text('TO BE FILLED BY TEAM')
            self.assertTrue(any('Unresolved team placeholder' in issue for issue in checker.check(root)))
