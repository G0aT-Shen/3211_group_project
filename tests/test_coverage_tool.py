"""Coverage metrics must count the selected files and report skipped tests."""
import contextlib
import importlib.util
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


SPEC = importlib.util.spec_from_file_location(
    'coverage_tool', Path(__file__).resolve().parents[1] / 'tools/check_coverage.py')
coverage_tool = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(coverage_tool)


class CoverageToolTests(unittest.TestCase):
    def setUp(self):
        # trace.runfunc clears the tracing hook; preserve an outer coverage run.
        self.addCleanup(sys.settrace, sys.gettrace())

    def test_package_initializers_are_selected_by_path(self):
        """An unrelated __init__.py cannot suppress the selected package initializer."""
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            selected = root / 'model' / '__init__.py'
            unrelated = root / 'other' / '__init__.py'
            for source in (selected, unrelated):
                source.parent.mkdir()
                source.write_text('VALUE = 1\n', encoding='utf-8')
            tracer = coverage_tool.ModelTrace([selected])

            def execute_sources():
                for source in (unrelated, selected):
                    code = compile(source.read_text(encoding='utf-8'), str(source), 'exec')
                    exec(code, {'__file__': str(source)})

            tracer.runfunc(execute_sources)
            self.assertEqual(tracer.results().counts, {(str(selected), 1): 1})

    def test_unreported_source_excludes_synthetic_line_zero(self):
        """The omitted-file denominator includes actual source lines only."""
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'sample.py'
            source.write_text('VALUE = 1\n', encoding='utf-8')
            with patch.object(coverage_tool.trace, '_find_executable_linenos',
                              return_value={0: 1, 1: 1}):
                self.assertEqual(coverage_tool.coverage_counts(
                    source, Path(folder) / 'missing.cover'), (0, 1))

    def test_report_includes_skips_and_replaces_stale_counts(self):
        """A skipped test stays visible, and a stale hit cannot inflate coverage."""
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'model').mkdir()
            (root / 'model' / 'sample.py').write_text('VALUE = 1\n', encoding='utf-8')
            reports = root / '.coverage'
            reports.mkdir()
            (reports / 'model.sample.cover').write_text('    1: VALUE = 1\n', encoding='utf-8')
            result = unittest.TestResult()
            result.testsRun = 1
            result.skipped.append((None, 'platform unavailable'))
            with patch.object(coverage_tool, 'ROOT', root), \
                    patch.object(coverage_tool, 'run_tests', return_value=result), \
                    contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(coverage_tool.main(), 0)
            report = (root / 'coverage_report.txt').read_text(encoding='utf-8')
            self.assertIn('Tests: 1, failures: 0, errors: 0\nSkipped: 1\n', report)
            self.assertRegex(report, r'model/sample\.py\s+0\s+1\s+0\.00%')
