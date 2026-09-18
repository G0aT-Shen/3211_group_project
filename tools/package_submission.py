"""Build a review ZIP, or a final ZIP only after the release gate passes."""
import argparse
from datetime import datetime
from pathlib import Path
import zipfile
from check_submission import ROOT, check


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--draft', action='store_true', help='Create an explicitly incomplete review archive')
    args = parser.parse_args()
    issues = check()
    if issues and not args.draft:
        print('Final packaging refused. Run tools/check_submission.py or use --draft for review.')
        return 1
    destination = ROOT / 'submission'
    destination.mkdir(exist_ok=True)
    stamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    path = destination / f'PIM_{"REVIEW_DRAFT" if args.draft else "FINAL"}_{stamp}.zip'
    files = []
    for package in ['model', 'controller', 'cli', 'storage', 'view', 'tests']:
        files.extend((ROOT / package).glob('*.py'))
    for name in ['main.py','README.md','deploy_readme.md','pyproject.toml','LICENSE',
                 'coverage_report.txt','coverage_report.pdf','requirements_coverage.md','requirements_coverage.pdf','tools/check_coverage.py',
                 'tools/check_submission.py','tools/package_submission.py','tools/demo_session.py']:
        files.append(ROOT / name)
    files.append(ROOT / 'docs/review_status.example.json')
    files.extend((ROOT / 'docs').glob('*.md'))
    files.extend((ROOT / 'docs').glob('*.mermaid'))
    files.extend((ROOT / 'output/pdf').glob('*.pdf'))
    files.extend((ROOT / 'output/presentation').glob('*.pdf'))
    files.extend((ROOT / 'output/presentation').glob('*.pptx'))
    files.extend((ROOT / 'output/demo').glob('*.mp4'))
    files.extend((ROOT / 'output/demo').glob('*.json'))
    with zipfile.ZipFile(path,'x',compression=zipfile.ZIP_DEFLATED) as archive:
        for source in sorted(set(files)):
            if source.is_file():
                archive.write(source, str(source.relative_to(ROOT)))
        if args.draft:
            archive.writestr('REVIEW_DRAFT_NOT_FINAL.txt', 'Open submission items:\n' + '\n'.join(issues))
        else:
            archive.write(ROOT / 'submission_inputs/Honour Declaration.pdf','Honour Declaration.pdf')
            archive.write(ROOT / 'submission_inputs/presentation_recording.mp4','presentation_recording.mp4')
    with zipfile.ZipFile(path) as archive:
        if archive.testzip() is not None:
            raise RuntimeError('Archive integrity check failed')
    print(path)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
