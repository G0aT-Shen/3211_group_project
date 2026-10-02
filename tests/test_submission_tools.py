"""Release-gate regression checks protect against incomplete final packaging."""
import importlib.util
import contextlib
import hashlib
import io
import json
from pathlib import Path
import shutil
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch
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
    def test_nested_mp4_is_reported_as_invalid_without_crashing(self):
        """Malformed box nesting cannot crash either duration parsing or the release gate."""
        payload = mp4(1)
        for _ in range(1100):
            payload = struct.pack('>I4s', len(payload) + 8, b'moov') + payload
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path = root / 'output/demo/system_demo.mp4'
            path.parent.mkdir(parents=True)
            path.write_bytes(payload)
            self.assertIsNone(checker.mp4_duration(path))
            self.assertTrue(any('Invalid or excessive duration' in issue for issue in checker.check(root)))

    def test_mp4_extended_and_version_one_headers_still_work(self):
        """Legal 64-bit box sizes, v1 timestamps and end-of-file sizes remain supported."""
        body = b'\x01' + b'\0' * 19 + struct.pack('>IQ', 1000, 124000)
        mvhd = struct.pack('>I4sQ', 1, b'mvhd', len(body) + 16) + body
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'valid.mp4'
            for payload in [mp4(124), struct.pack('>I4s', 0, b'moov') + mvhd]:
                path.write_bytes(payload)
                self.assertEqual(checker.mp4_duration(path), 124)

    def test_draft_archive_preserves_authoring_tools_and_runtime_sources(self):
        """The extracted archive contains the documented regeneration entry points."""
        source_root = Path(__file__).resolve().parents[1]
        spec = importlib.util.spec_from_file_location('submission_packager', source_root / 'tools/package_submission.py')
        packager = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {'check_submission': checker}):
            spec.loader.exec_module(packager)
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / 'source'
            root.mkdir()
            shutil.copyfile(source_root / 'main.py', root / 'main.py')
            for package in ['model', 'controller', 'cli', 'storage', 'view', 'tests', 'tools']:
                shutil.copytree(source_root / package, root / package,
                                ignore=shutil.ignore_patterns('__pycache__'))
            with patch.object(packager, 'ROOT', root), \
                    patch.object(packager, 'check', return_value=['Test fixture: pending review']), \
                    patch.object(sys, 'argv', ['package_submission.py', '--draft']), \
                    contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(packager.main(), 0)
            extracted = Path(folder) / 'extracted'
            with zipfile.ZipFile(next((root / 'submission').glob('*.zip'))) as archive:
                archive.extractall(extracted)
            for name in ['build_slides.mjs', 'render_documents.py', 'render_demo_frames.py', 'encode_demo.swift']:
                self.assertEqual((extracted / 'tools' / name).read_bytes(), (source_root / 'tools' / name).read_bytes())
            self.assertTrue((extracted / 'main.py').is_file())
            self.assertTrue((extracted / 'REVIEW_DRAFT_NOT_FINAL.txt').is_file())

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
