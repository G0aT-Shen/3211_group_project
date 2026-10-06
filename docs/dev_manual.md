# Developer Manual
COMP3211 PIM | Version 0.2 | macOS / Windows | 5 October 2026

## 1. Environment
The current 5 October requirements audit was run on macOS with CPython 3.9.6 and 3.12.14: all 88 tests passed on both, with no failures, errors or skips, and syntax compilation passed. The root coverage report was regenerated with 3.12.14 (439/443 executable model lines, 99.10%). The preceding review revision was verified on Windows with CPython 3.12.10 and 3.12.14. Windows and hosted CI were not run for the current revision. Python 3.11 is covered by the CI configuration but was not installed locally. The course requires Java or Python, not a particular Python version.

Use VS Code and open the repository folder. Select an installed Python interpreter in the Python extension, or use Terminal without any IDE. The application and automated tests use only Python standard libraries; pip install is unnecessary. pyproject.toml is metadata; this repository runs directly from source, not as a published installable distribution.

## 2. Build, run and debug
```bash
python3 --version
python3 -m compileall -q model controller cli storage view main.py
python3 main.py
python3 -m pdb main.py
```
Python requires no separate binary build. compileall checks syntax. In pdb, use b cli/repl.py:75 (adjust to the current line) or b model/manager.py:46 to stop at dispatch/model operations; c continues and n steps. For IDE debugging, run main.py with the repository as working directory. Avoid debugging with real personal information or overwriting a valuable .pim file.

## 3. Tests and honest coverage
```bash
python3 -m unittest discover -v
python3 tools/check_coverage.py
```
On Windows with the Python launcher installed, replace `python3` with `py -3` in these commands. A missing `python` command on PATH does not require installing project dependencies.

The first command returns nonzero on failure. The coverage tool also runs the suite, generates annotated .coverage/model.*.cover files and rewrites coverage_report.txt at the source root. It uses stdlib trace with show_missing=True and explicitly counts executed plus missed executable lines. Never use the old summary command as proof of 100%: without missing-line analysis it counts only hit lines.

The report includes every model .py file. It excludes CLI, controller, storage, view and test lines from the model denominator, but tests still exercise those components. Tracing selects model files by path, so an unrelated package's `__init__.py` cannot hide the model's package initialization. Abstract/protocol declarations remain in the denominator. No branch-coverage claim is made. Changes in Python bytecode/source analysis can slightly alter line denominators across versions. The report lists skipped tests separately.

Tests include domain invalid-input checks, round-trips of all record types, ID persistence after deletion, search precedence, atomic file replacement failure, cancelled confirmations and a real subprocess CLI workflow. .github/workflows/tests.yml configures Python 3.9/3.11/3.12 on Ubuntu. The Windows results in this review came from local runs; a local pass does not prove a hosted CI run has passed.

Windows runs skip the POSIX FIFO test and, only when the OS reports missing privileges, the real symlink test. A separate test always checks that storage rejects symlink paths for both save and load. Console regressions verify that limited output encodings preserve the session and saved Unicode, while search regressions cover literal trailing backslashes, shell escapes, concatenated quotes and malformed quotes. The acceptance workflow compares complete saved records, then starts a new application process to verify restoration of every field and continued ID allocation. Model regressions also prevent mutation through __dict__/vars, assert exact edits and unaffected records, and check sorting and Unicode case folding.

tests/test_review_fixes.py covers interrupted IO and allocation, the last usable ID and exhaustion round-trips, and rejecting a real named pipe without blocking. Submission-tool tests also check malformed MP4 nesting, valid extended headers and authoring-tool preservation after archive extraction.

## 4. Source navigation and extension
model contains all domain types, shared field schemas, collection rules and search AST/parser. controller exposes compatibility imports. cli parses shell-like commands and orchestrates model/storage/view. storage performs bounded strict JSON IO; view formats text. main.py starts the REPL.

To add a PIR type, define an immutable model subclass, register it in model/factory.py, extend the field set in model/search.py, add command examples/help, and add tests/traceability. Keep the model free of IO. To extend file format, introduce a deliberate schema migration and tests; do not silently accept unknown fields or invalid next_id.

## 5. Document and release generation
Markdown files under docs are editable sources. Formal submission uses their PDF exports. Document rendering and slides are authoring tools, separate from the standard-library product. The render builder uses ReportLab; slides use the artifact authoring runtime. Those tools are not imported by the application. Pre-generated PDFs/PPTX are provided so users do not need them to run the project.

Edit `docs/team_members.json` with the agreed display names, for example `{"members": ["Alice", "Bob"]}` (these are syntax examples, not actual member identities). An empty list deliberately keeps the deck a draft. Regenerate the coverage report before building slides; slide verification numbers come directly from that report. The builder locates the repository relative to its own script and can run from any working directory.

```bash
node tools/build_slides.mjs --help
node tools/build_slides.mjs
```

The builder defaults to the current user's bundled authoring runtime. For another installation set `PIM_RUNTIME_DEPS` to the dependencies directory containing node/node_modules and python/bin/python3, and `PIM_PRESENTATION_SKILL` to the presentation tools directory containing container_tools. Optional `PIM_PYTHON` overrides the validator executable path; `PIM_SOFFICE` overrides the LibreOffice executable used to export PDF (it may be `soffice` when available on PATH). Missing dependencies fail before published files are replaced. The builder validates the PPTX, exports its PDF, then writes both outputs and output/presentation/build_manifest.json. The manifest records SHA-256 hashes of both outputs, team_members.json and coverage_report.txt.

```bash
python3 tools/check_submission.py
python3 tools/package_submission.py
```
The submission checker reports missing human deliverables and fails until they are present and unresolved placeholders are resolved. It inspects the final PPTX slide/notes text, verifies the displayed member list against team_members.json, and checks the build manifest so an older PDF or deck cannot be silently mixed with new configuration or coverage data. Rebuild the pair after changing any recorded input or editing either output. The packaging tool includes the member configuration, manifest and all .py/.mjs/.swift authoring tools directly under tools/, and refuses to label an incomplete archive as final. It excludes .git, caches, local .pim files and private build outputs. Group members must complete the official Honour Declaration, agree contributions, verify lecture formatting and record the required presentations.

Documentation PDFs, the root requirements report and coverage report were regenerated for the current code. Presentation PDF/PPTX files remain the earlier snapshot; rebuild that pair before final submission, then record the team's real review results. PDF/demo authoring scripts use macOS fonts, PTY or AVFoundation; application tests do not verify those authoring dependencies. The original course description requires a model line-coverage report but does not require 100% line coverage; abstract/protocol declaration lines remain in this report's denominator.

## 6. Data operations and known boundaries
Saving flushes and fsyncs a temporary file, then replaces the destination. Failure preserves prior target bytes and attempts to remove the temporary artifact. If the operating system also refuses cleanup, the error reports the temporary path for later manual removal. Path inspection and cleanup errors are translated into StorageError so the CLI remains usable. Files are not encrypted. Single-process usage is assumed; no advisory locking or cross-machine time conversion is implemented. Application limits and local timestamp interpretation are explicit in the SRS/user manual.

GenAI-assisted material must be disclosed. docs/ai_usage.md records the scope and correction history for the group to transfer into its official declaration. Do not fabricate approvals, signatures, contribution percentages or test results.
