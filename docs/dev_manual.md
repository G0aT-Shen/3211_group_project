# Developer Manual
COMP3211 PIM | Version 0.2 | macOS | 18 September 2026

## 1. Environment
Platform documented: macOS. Verified interpreters: CPython 3.9.6 and CPython 3.12.14. Python 3.11 is included in the CI configuration but was not installed locally for this revision. The course requires Java or Python, not a particular Python version.

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
The first command returns nonzero on failure. The coverage tool also runs the suite, generates annotated .coverage/model.*.cover files and rewrites coverage_report.txt at the source root. It uses stdlib trace with show_missing=True and explicitly counts executed plus missed executable lines. Never use the old summary command as proof of 100%: without missing-line analysis it counts only hit lines.

The report includes every model .py file. It excludes CLI, controller, storage, view and test lines from the model denominator, but tests still exercise those components. Abstract/protocol declarations remain in the denominator. No branch-coverage claim is made. Changes in Python bytecode/source analysis can slightly alter line denominators across versions.

Tests include domain invalid-input checks, round-trips of all record types, ID persistence after deletion, search precedence, atomic file replacement failure, cancelled confirmations and a real subprocess CLI workflow. .github/workflows/tests.yml configures Python 3.9/3.11/3.12 on Ubuntu. A local pass does not prove a hosted CI run has passed.

## 4. Source navigation and extension
model contains all domain types, shared field schemas, collection rules and search AST/parser. controller exposes compatibility imports. cli parses shell-like commands and orchestrates model/storage/view. storage performs bounded strict JSON IO; view formats text. main.py starts the REPL.

To add a PIR type, define an immutable model subclass, register it in model/factory.py, extend the field set in model/search.py, add command examples/help, and add tests/traceability. Keep the model free of IO. To extend file format, introduce a deliberate schema migration and tests; do not silently accept unknown fields or invalid next_id.

## 5. Document and release generation
Markdown files under docs are editable sources. Formal submission uses their PDF exports. Document rendering and slides are authoring tools, separate from the standard-library product. The render builder uses ReportLab; slides use the artifact authoring runtime. Those tools are not imported by the application. Pre-generated PDFs/PPTX are provided so users do not need them to run the project.

```bash
python3 tools/check_submission.py
python3 tools/package_submission.py
```
The submission checker reports missing human deliverables and fails until they are present and unresolved placeholders are resolved. The packaging tool refuses to label an incomplete archive as final. It excludes .git, caches, local .pim files and private build outputs. Group members must complete the official Honour Declaration, agree contributions, verify lecture formatting and record the required presentations.

## 6. Data operations and known boundaries
Saving flushes and fsyncs a temporary file, then replaces the destination. Failure preserves prior target bytes and attempts to remove the temporary artifact. If the operating system also refuses cleanup, the error reports the temporary path for later manual removal. Path inspection and cleanup errors are translated into StorageError so the CLI remains usable. Files are not encrypted. Single-process usage is assumed; no advisory locking or cross-machine time conversion is implemented. Application limits and local timestamp interpretation are explicit in the SRS/user manual.

GenAI-assisted material must be disclosed. docs/ai_usage.md records the scope and correction history for the group to transfer into its official declaration. Do not fabricate approvals, signatures, contribution percentages or test results.
