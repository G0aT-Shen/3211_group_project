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
    # Explicit patterns keep local records, credentials and caches out of archives.
    patterns = [f'{package}/*.py' for package in ('model', 'controller', 'cli', 'storage', 'view', 'tests')]
    patterns += [
        'main.py', 'run_windows.cmd', 'README.md', 'README.zh-CN.md', 'deploy_readme.md', 'deploy_readme.zh-CN.md',
        'pyproject.toml', '.gitattributes', 'LICENSE', 'coverage_report.txt', 'coverage_report.pdf',
        'requirements_coverage.md', 'requirements_coverage.pdf',
        'tools/*.py', 'tools/*.mjs', 'tools/*.swift',
        'docs/review_status.example.json', 'docs/team_members.json', 'docs/*.md', 'docs/*.mermaid',
        'output/pdf/*.pdf', 'output/presentation/*.pdf', 'output/presentation/*.pptx',
        'output/presentation/build_manifest.json', 'output/demo/*.mp4', 'output/demo/*.json',
        '.github/workflows/*.yml',
    ]
    files = {source for pattern in patterns for source in ROOT.glob(pattern) if source.is_file()}
    with zipfile.ZipFile(path,'x',compression=zipfile.ZIP_DEFLATED) as archive:
        for source in sorted(files):
            archive.write(source, source.relative_to(ROOT).as_posix())
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
