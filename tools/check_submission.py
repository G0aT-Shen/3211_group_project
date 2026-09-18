"""Read-only release gate. Exits nonzero until every required item is present."""
import argparse
import json
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    'main.py', 'README.md', 'requirements_coverage.md', 'requirements_coverage.pdf', 'coverage_report.txt', 'coverage_report.pdf',
    'output/pdf/SRS.pdf', 'output/pdf/design.pdf', 'output/pdf/dev_manual.pdf',
    'output/pdf/user_manual.pdf', 'output/pdf/requirements_coverage.pdf',
    'output/demo/system_demo.mp4', 'output/presentation/PIM_presentation.pdf',
    'submission_inputs/Honour Declaration.pdf', 'submission_inputs/presentation_recording.mp4',
    'submission_inputs/review_status.json',
]
APPROVALS = ['lecture04_structure_checked', 'member_fields_completed',
             'contributions_agreed', 'official_declaration_signed',
             'every_presenter_face_and_id_verified', 'each_member_speaks_at_least_one_minute',
             'documents_match_final_implementation']


def mp4_duration(path):
    """Read mvhd duration from an ISO base media file without external libraries."""
    def scan(stream, start, end):
        offset = start
        while offset + 8 <= end:
            stream.seek(offset)
            size, kind = struct.unpack('>I4s', stream.read(8))
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
                result = scan(stream, offset + header, offset + size)
                if result is not None:
                    return result
            if kind == b'mvhd':
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
    with path.open('rb') as stream:
        return scan(stream, 0, path.stat().st_size)


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
        if path.is_file() and 'TO BE FILLED BY TEAM' in path.read_text(encoding='utf-8'):
            issues.append('Unresolved team placeholder: ' + name)
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
