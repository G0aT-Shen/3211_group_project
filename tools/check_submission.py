"""Read-only release gate. Exits nonzero until every required item is present."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    'main.py', 'README.md', 'requirements_coverage.md', 'requirements_coverage.pdf', 'coverage_report.txt', 'coverage_report.pdf',
    'output/pdf/SRS.pdf', 'output/pdf/design.pdf', 'output/pdf/dev_manual.pdf',
    'output/pdf/user_manual.pdf', 'output/pdf/requirements_coverage.pdf',
    'output/demo/system_demo.mp4', 'output/presentation/PIM_presentation.pdf',
    'output/presentation/PIM_presentation.pptx', 'docs/team_members.json',
    'output/presentation/build_manifest.json',
    'submission_inputs/Honour Declaration.pdf', 'submission_inputs/presentation_recording.mp4',
    'submission_inputs/review_status.json',
]
APPROVALS = ['lecture04_structure_checked', 'member_fields_completed',
             'contributions_agreed', 'official_declaration_signed',
             'every_presenter_face_and_id_verified', 'each_member_speaks_at_least_one_minute',
             'documents_match_final_implementation']
TEAM_MARKER = 'TO BE FILLED BY TEAM'
PRESENTATION_INPUTS = ['output/presentation/PIM_presentation.pptx',
                       'output/presentation/PIM_presentation.pdf',
                       'docs/team_members.json', 'coverage_report.txt']


def presentation_issues(root):
    """Inspect the shipped slides and notes, including text split across XML runs."""
    issues, members = [], []
    config = root / 'docs/team_members.json'
    if config.is_file():
        try:
            data = json.loads(config.read_text(encoding='utf-8'))
            if (not isinstance(data, dict) or set(data) != {'members'}
                    or not isinstance(data['members'], list)
                    or not data['members']
                    or any(not isinstance(name, str) or not name.strip()
                           or name != name.strip() or TEAM_MARKER in name
                           or any(ord(char) < 32 for char in name)
                           for name in data['members'])
                    or len(set(data['members'])) != len(data['members'])):
                raise ValueError('members must be a nonempty list of unique, nonblank names')
            members = data['members']
            for name in members:
                name.encode('utf-8')
        except (OSError, ValueError, UnicodeError) as exc:
            issues.append('Invalid team member configuration: ' + str(exc))
    name = 'output/presentation/PIM_presentation.pptx'
    deck = root / name
    if deck.is_file():
        try:
            slides, notes = [], []
            with zipfile.ZipFile(deck) as archive:
                for part in archive.namelist():
                    if re.fullmatch(r'ppt/(slides/slide|notesSlides/notesSlide)\d+\.xml', part):
                        document = ET.fromstring(archive.read(part))
                        # Join text runs within each paragraph, not across paragraphs.
                        paragraphs = [''.join(node.itertext()) for node in document.iter()
                                      if node.tag.rsplit('}', 1)[-1] == 'p']
                        (slides if part.startswith('ppt/slides/') else notes).extend(paragraphs)
            if not slides:
                raise ValueError('no slide text found')
            if any(TEAM_MARKER in text for text in slides + notes):
                issues.append('Unresolved team placeholder: ' + name)
            if members and 'Group members: ' + ', '.join(members) not in slides:
                issues.append(f'Presentation members do not match docs/team_members.json; regenerate {name}')
        except (OSError, ValueError, zipfile.BadZipFile, ET.ParseError) as exc:
            issues.append('Invalid presentation: ' + str(exc))
    manifest = root / 'output/presentation/build_manifest.json'
    if manifest.is_file():
        try:
            data = json.loads(manifest.read_text(encoding='utf-8'))
            if (not isinstance(data, dict) or set(data) != {'schema_version', 'sha256'}
                    or type(data['schema_version']) is not int or data['schema_version'] != 1
                    or not isinstance(data['sha256'], dict)
                    or set(data['sha256']) != set(PRESENTATION_INPUTS)):
                raise ValueError('expected schema_version=1 and hashes of all presentation inputs')
            for name in PRESENTATION_INPUTS:
                path = root / name
                if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != data['sha256'][name]:
                    issues.append('Stale presentation build: ' + name + '; rebuild slides and PDF together')
        except (OSError, ValueError, UnicodeError) as exc:
            issues.append('Invalid presentation build manifest: ' + str(exc))
    return issues


def mp4_duration(path):
    """Read mvhd duration from an ISO base media file without external libraries."""
    def scan(stream, start, end, in_moov=False):
        offset = start
        while offset + 8 <= end:
            stream.seek(offset)
            box_header = stream.read(8)
            if len(box_header) != 8:
                return None
            size, kind = struct.unpack('>I4s', box_header)
            header = 8
            if size == 1:
                data = stream.read(8)
                if len(data) != 8:
                    return None
                size = struct.unpack('>Q', data)[0]
                header = 16
            if size == 0:
                size = end - offset
            if size < header or offset + size > end:
                return None
            if kind == b'moov':
                # moov is a top-level box; nested moov boxes are malformed.
                if in_moov:
                    return None
                result = scan(stream, offset + header, offset + size, in_moov=True)
                if result is not None:
                    return result
            if kind == b'mvhd' and in_moov:
                data = stream.read(min(size - header, 32))
                if len(data) < 20:
                    return None
                if data[0] == 0:
                    scale, duration = struct.unpack('>II', data[12:20])
                elif data[0] == 1 and len(data) >= 32:
                    scale, duration = struct.unpack('>IQ', data[20:32])
                else:
                    return None
                return duration / scale if scale else None
            offset += size
        return None
    try:
        with path.open('rb') as stream:
            return scan(stream, 0, path.stat().st_size)
    except (OSError, ValueError, struct.error):
        return None


def check(root=ROOT):
    issues = []
    for name in REQUIRED:
        path = root / name
        if not path.is_file() or not path.stat().st_size:
            issues.append('Missing or empty: ' + name)
        elif path.suffix == '.pdf' and path.read_bytes()[:5] != b'%PDF-':
            issues.append('Invalid PDF signature: ' + name)
    for name, maximum in [('output/demo/system_demo.mp4', 240), ('submission_inputs/presentation_recording.mp4', 300)]:
        path = root / name
        if path.is_file():
            duration = mp4_duration(path)
            if duration is None or not 0 < duration <= maximum:
                issues.append(f'Invalid or excessive duration: {name} ({duration}, maximum {maximum}s)')
    status_path = root / 'submission_inputs/review_status.json'
    if status_path.is_file():
        try:
            status = json.loads(status_path.read_text(encoding='utf-8'))
            if not isinstance(status, dict):
                raise ValueError('must be an object')
            for name in APPROVALS:
                if status.get(name) is not True:
                    issues.append('Human review pending: ' + name)
        except (ValueError, UnicodeError) as exc:
            issues.append('Invalid review status: ' + str(exc))
    else:
        issues.extend('Human review pending: ' + name for name in APPROVALS)
    # Markers in official doc sources must be resolved before regenerating final PDFs.
    for name in ['docs/SRS.md', 'docs/presentation_script.md']:
        path = root / name
        if path.is_file() and TEAM_MARKER in path.read_text(encoding='utf-8'):
            issues.append('Unresolved team placeholder: ' + name)
    issues.extend(presentation_issues(root))
    return issues


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args()
    issues = check(args.root)
    if issues:
        print('NOT READY FOR FINAL SUBMISSION')
        print('\n'.join('- ' + issue for issue in issues))
        raise SystemExit(1)
    print('Required files and recorded human approvals are present. Review their content before submitting.')
