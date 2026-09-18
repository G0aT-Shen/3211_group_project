"""Run tests and report actual executed / executable model lines using stdlib trace."""
import contextlib
import io
from pathlib import Path
import re
import sys
import trace
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def run_tests():
    suite = unittest.defaultTestLoader.discover(str(ROOT / 'tests'), top_level_dir=str(ROOT))
    return unittest.TextTestRunner(verbosity=1).run(suite)


def coverage_counts(source: Path, report: Path) -> tuple[int, int]:
    """Count a trace report, treating an omitted source file as entirely missed."""
    if report.exists():
        covered = missing = 0
        for line in report.read_text(encoding='utf-8').splitlines():
            if re.match(r'\s*\d+:', line):
                covered += 1
            elif line.startswith('>>>>>>'):
                missing += 1
        return covered, covered + missing
    executable = trace._find_executable_linenos(str(source))
    source_lines = source.read_text(encoding='utf-8').splitlines()
    total = sum(1 for number in executable
                if number <= len(source_lines) and trace.PRAGMA_NOCOVER not in source_lines[number - 1])
    return 0, total


def main():
    tracer = trace.Trace(count=True, trace=False, ignoredirs=[sys.base_prefix, sys.prefix])
    result = tracer.runfunc(run_tests)
    folder = ROOT / '.coverage'
    folder.mkdir(exist_ok=True)
    for stale in folder.glob('model.*.cover'):
        stale.unlink()
    # show_missing=True is essential: without it trace reports only executed lines.
    with contextlib.redirect_stdout(io.StringIO()):
        tracer.results().write_results(show_missing=True, summary=True, coverdir=str(folder))
    lines = ['Model line coverage (stdlib trace; includes unexecuted executable lines)',
             f'Python {sys.version.split()[0]}', f'Tests: {result.testsRun}, failures: {len(result.failures)}, errors: {len(result.errors)}',
             'Scope: every .py file in model/. CLI/controller/storage/view/tests are excluded from denominator.',
             'Definition: executed executable lines / all executable lines identified by trace.',
             'No branch-coverage claim. Abstract method and protocol declaration lines remain in denominator.',
             '', 'File                              Executed  Executable  Coverage']
    totals = [0, 0]
    for source in sorted((ROOT / 'model').glob('*.py')):
        report = folder / ('model.' + source.stem + '.cover')
        covered, total = coverage_counts(source, report)
        totals[0] += covered
        totals[1] += total
        lines.append(f'model/{source.name:<27} {covered:>6} {total:>11} {100 * covered / total if total else 100:>8.2f}%')
    lines.append(f'TOTAL                             {totals[0]:>6} {totals[1]:>11} {100 * totals[0] / totals[1]:>8.2f}%')
    report_text = '\n'.join(lines) + '\n'
    (ROOT / 'coverage_report.txt').write_text(report_text, encoding='utf-8')
    print(report_text)
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    raise SystemExit(main())
