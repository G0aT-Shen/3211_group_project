"""Release-gate regression checks protect against incomplete final packaging."""
import importlib.util
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest
import zipfile

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


def pptx(path, text='Group members: Alice', notes=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, 'w') as archive:
        archive.writestr('ppt/slides/slide1.xml',
                         '<slide><p><t>' + text + '</t></p></slide>')
        if notes is not None:
            archive.writestr('ppt/notesSlides/notesSlide1.xml',
                             '<notes><p><t>' + notes + '</t></p></notes>')


def manifest(root):
    names = ['output/presentation/PIM_presentation.pptx',
             'output/presentation/PIM_presentation.pdf',
             'docs/team_members.json', 'coverage_report.txt']
    hashes = {name: hashlib.sha256((root/name).read_bytes()).hexdigest() for name in names}
    path = root/'output/presentation/build_manifest.json'
    path.write_text(json.dumps({'schema_version': 1, 'sha256': hashes}))


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
            (root/'docs').mkdir(exist_ok=True)
            (root/'docs/team_members.json').write_text('{"members": ["Alice"]}')
            pptx(root/'output/presentation/PIM_presentation.pptx')
            manifest(root)
            self.assertEqual(checker.check(root), [])
            (root/'output/demo/system_demo.mp4').write_bytes(mp4(241))
            self.assertTrue(any('excessive duration' in issue for issue in checker.check(root)))
            status.write_text('[]')
            self.assertTrue(any('Invalid review status' in issue for issue in checker.check(root)))

    def test_final_deck_rejects_placeholders_and_stale_member_names(self):
        """Editing the script or configuration cannot hide an unfinished final PPTX."""
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root/'docs').mkdir()
            (root/'docs/presentation_script.md').write_text('Presenters: Alice')
            (root/'docs/team_members.json').write_text('{"members": ["Alice"]}')
            deck = root/'output/presentation/PIM_presentation.pptx'
            pptx(deck, 'TO BE </t><t>FILLED BY TEAM')
            self.assertTrue(any('Unresolved team placeholder' in issue and '.pptx' in issue
                                for issue in checker.check(root)))
            pptx(deck, 'Bob')
            self.assertTrue(any('members do not match' in issue for issue in checker.check(root)))
            pptx(deck, 'Group members: Alice', 'TO BE FILLED BY TEAM')
            self.assertTrue(any('Unresolved team placeholder' in issue and '.pptx' in issue
                                for issue in checker.check(root)))
            deck.write_bytes(b'not a zip')
            self.assertTrue(any('Invalid presentation' in issue for issue in checker.check(root)))

    def test_presentation_manifest_rejects_stale_pdf_and_config(self):
        """A valid PPTX cannot mask a PDF or member configuration from an older build."""
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for name in checker.REQUIRED:
                path = root/name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b'%PDF-test' if path.suffix == '.pdf' else b'test')
            (root/'docs/team_members.json').write_text('{"members": ["Alice"]}')
            pptx(root/'output/presentation/PIM_presentation.pptx')
            manifest(root)
            self.assertEqual(checker.presentation_issues(root), [])
            (root/'output/presentation/PIM_presentation.pdf').write_bytes(b'%PDF-older')
            self.assertTrue(any('Stale presentation build' in issue and '.pdf' in issue
                                for issue in checker.presentation_issues(root)))
            manifest(root)
            (root/'docs/team_members.json').write_text('{"members": ["Al"]}')
            issues = checker.presentation_issues(root)
            self.assertTrue(any('Stale presentation build' in issue for issue in issues))
            self.assertTrue(any('members do not match' in issue for issue in issues))


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
