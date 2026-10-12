# Deployment and implementation log

**English** | [中文](deploy_readme.zh-CN.md)

This file records project implementation, verification, and documentation updates in chronological order. Times follow the local machine (Asia/Hong_Kong).

## 2026-09-18

1. Inspected the local project directory and confirmed the original content: the course project PDF and a Chinese summary of the specification.
2. Checked the GitHub repository `G0aT-Shen/3211_group_project`, initialised local Git, associated `origin`, synced the `main` branch, and verified that local and remote commits matched.
3. Read `docs/system_design.md`. Used its Python 3.11+, standard-library, MVC-layered, four-PIR-types, JSON `.pim`, search-expression, and T01–T05 task breakdown as the implementation blueprint; design assumptions in that document were not treated as additional user instructions.
4. Created the model layer: the `PIR` abstract base class plus `TextPIR`, `TaskPIR`, `EventPIR`, and `ContactPIR` under `model/`, along with domain exceptions and date-parsing utilities.
5. Created the controller and storage layers: `PIMManager`, `PIRFactory`, and the JSON `Storage`, implementing monotonic-integer IDs, CRUD, search orchestration, serialization, and `.pim` file read/write.
6. Created the command-interaction and view layers: `CommandParser`, the recursive-descent `SearchParser`, the search AST, `Printer`, `Repl`, and `main.py`. Supported `contains`, time comparisons, `&&`, `||`, `!`, parentheses, and the four PIR commands.
7. Created 12 standard-library `unittest` tests covering the model, search, controller, and storage; the first run exposed a PEP 604 union-annotation incompatibility on the current macOS Python 3.9, after which deferred annotations were added for Python 3.9+ compatibility.
8. Verification result: `python3 -m unittest discover -v` passed 12/12; a CLI smoke test completed the full add, search, edit, print, save, delete, load, and exit flow.
9. Generated the coverage summary with `python3 -m trace --count --summary --coverdir .coverage --module unittest discover > coverage_report.txt`; the trace detail directory was ignored and the root summary kept as a deliverable.
10. Updated `README.md` with the environment, run commands, CLI examples, and test/coverage commands; this file is used to keep recording each later change.
11. Fixed the field mapping from `edit event --start` to the model's `start_time`, allowed trailing spaces in search expressions, and changed the coverage command to `--coverdir .coverage` to avoid polluting the system Python installation directory.
12. Final verification: 12 unit tests passed; `compileall` reported no syntax errors; the coverage summary generated successfully; the working tree contained only this round's implementation, documentation, and test additions — no remote push was performed.

## 2026-09-18: Completion against the original requirements and marking rubric (0.2)

1. Re-checked the original course PDF item by item against US1–US11, the five deliverables, and the Appendix A rubric. Kept the original plan and added a historical-version note to `docs/system_design.md`; the course allows Python or Java, so Python 3.11 is not a mandatory version and JUnit is not forbidden.
2. Added `model/factory.py`, `model/manager.py`, and `model/search.py`, concentrating collections, IDs, field rules, and the search AST/parser inside an independent `model` package. The controller and the legacy CLI search path keep compatibility exports, and the model depends on neither console nor file IO.
3. PIR instances reject ordinary attribute mutation and deletion after construction, and return field copies and read-only collection views. Addition returns a new object carrying the allocated ID; an edit is atomically replaced only after full validation, and a failure neither modifies the old record nor consumes an ID.
4. Fixed real problems: crashes on invalid print/delete IDs, false success reports for unknown edit fields, and distortion of quoted multi-word searches. Duplicate, missing, unknown, and incompatible fields are rejected, with consistent casing, the `start` alias, strict minute-precision dates, ASCII positive-integer IDs, and command-argument counts.
5. Search supports all text and time fields, the type field, logical precedence, and parentheses. Fields, operators, and dates are validated before iterating records, and an empty collection still rejects invalid conditions. Missing-field, negation, and Unicode-casefold semantics are explicit, and command length, search length, and nesting depth are bounded.
6. `.pim` uses strict UTF-8 JSON with an exact schema, unique IDs and JSON keys, an incrementing `next_id`, and rejection of non-finite numbers and symbolic links; the file limit is 10 MiB. Saving uses a same-directory temporary file with flush/fsync and `os.replace`; loading replaces the current state only after full validation.
7. Added confirmations for overwriting a file, discarding unsaved data via load, and discarding changes on exit; EOF reports the unsaved state and Ctrl-C cancels the current line. Completed `help`, the user manual, and output descriptions.
8. The final boundary check reproduced an uncaught `OSError` from a long filename. Three regression tests were added (failing first, then passing), fixing the exception boundaries for path checks, overwrite checks, and temporary-file cleanup. A failed cleanup reports the leftover temporary path while the previous target stays intact; a real CLI long-filename save/load followed by the help/exit flow was verified.
9. Tests grew to 55, covering every field edit, date boundaries, logical combinations, corrupted files, atomic-replacement failure, cancellation confirmation, real subprocess US1–US11 flows, standard-library imports, model-layering constraints, and the missing-coverage-report fallback. They pass on CPython 3.9.6 and 3.12.14. A GitHub Actions 3.9/3.11/3.12 test matrix was configured.
10. Corrected the old coverage summary: the previous trace command did not count unexecuted lines in the denominator, so the earlier "100%" was not a complete coverage proof. `tools/check_coverage.py` uses `show_missing=True`, and the actual model line coverage is 411/413 (99.52%), including unexecuted abstract-method and Protocol-declaration lines, with no branch-coverage claim. Both `coverage_report.txt` and a PDF are provided at the root.
11. Wrote the numbered SRS, the current design/API contract, complete user and developer manuals, a bidirectional US-to-SRS checklist, the grading acceptance checklist, the AI-assistance record, and the presentation script. Updated the two standalone Mermaid files; the design PDF contains the architecture diagram, class-relation diagram, search and update sequence diagrams from one example, and a signature list generated from the Python AST.
12. Generated and checked the PDF documents, the 6-page editable PPTX, and the presentation PDF. Per-page rendering checks were run per the PDF/presentation skills, fixing inheritance/dependency arrows, heading pagination, and presentation-verification temporary paths. Authoring-tool dependencies are isolated from the pure-standard-library application and are not runtime or official-source dependencies.
13. `tools/demo_session.py` captures output from a real `main.py` subprocess and produces a console demo MP4 with an explicit provenance note, 124 seconds long (2:04) at 1600×1000. A video decoder was used to spot-check the opening, middle, and closing frames. The video has no narration and does not replace the required presenters-on-camera recording in which every presenter shows their student card.
14. Added submission-check and packaging tools: they check documents, video format/duration, real human-verification flags, and unfilled member markers; when materials are incomplete they refuse to build a FINAL archive and allow an explicit `--draft` REVIEW_DRAFT with an open-items list. The submission archive excludes `.git`, caches, personal `.pim` data, private build material, and authoring tools; the personal identification/declaration directory does not enter Git.
15. Updated the README's run commands, architecture, verification numbers, document/video links, and packaging method. The user confirmed that member names/roles, contribution shares, and Lecture 04 material are still unavailable and should stay as placeholders; no approvals, signatures, identities, or contribution shares were invented.
16. This round continued from local commit `0bbc0d2`; commit and remote-sync state follow Git history and `origin/main`. Formal submission still needs the team materials listed below; the current result is a runnable, reviewable version and does not promise full marks.
17. The final review archive passed its ZIP integrity check; after extraction to an independent temporary directory, the 55 tests, coverage generation, and `compileall` passed again, with model coverage still 411/413. The final packaging mode was verified to refuse execution because team materials are missing; the current deliverable is a REVIEW_DRAFT with an open-items list.

## 2026-09-18: GitHub Actions Python 3.11 coverage compatibility (0.3)

1. Inspected the raw job logs of GitHub Actions run `35301951751`. All 54 application tests passed on Python 3.11; the only failure was `python tools/check_coverage.py`: the standard-library `trace` did not produce a `.cover` file for `model/__init__.py`, and the old script raised `RuntimeError: Missing coverage for __init__.py`. Python 3.12 passed tests, coverage, and `compileall`; jobs cancelled by matrix fail-fast are not counted as test failures.
2. Added a regression test for missing reports: the coverage tool now counts source files without a generated `.cover` as zero-hit toward the executable-line denominator, instead of misreading `trace` output differences across Python versions as a program error. Stale `model.*.cover` artifacts are cleared before each run so an outdated report cannot mask the problem.
3. Set the GitHub Actions matrix to `fail-fast: false` so a failure in one environment still collects independent results for the other Python versions, and updated `actions/checkout` and `actions/setup-python` to the official v7 major versions.
4. Updated the automated test total to 55; coverage stayed at 411/413 (99.52%). README, the coverage text/PDF, and the 6-page presentation were updated in sync.
5. After commit `954c3a2` was pushed, GitHub Actions run `35303259313` completed: all three jobs (Python 3.9, 3.11, 3.12) succeeded, each passing the 55 tests, the coverage script, and `compileall`. The hosted-CI status was updated accordingly.

## 2026-09-18: Code-side Chinese-to-English cleanup and bilingual docs (0.4)

1. Verified that every shipped source file (`.py` under `model`, `cli`, `controller`, `storage`, `view`, `tests`, and `tools`) was already pure English: the translation had been completed earlier in commit `2d2d594` ("Use English CLI messages and help placeholders"), so no source file needed changing.
2. The only remaining Chinese lived in stale generated artifacts, which were regenerated rather than hand-edited:
   - `output/demo/session.json` — re-captured with `tools/demo_session.py` from the current English `main.py`.
   - `output/demo/system_demo.mp4` — installed Pillow into an isolated managed virtual environment, rendered frames with `tools/render_demo_frames.py`, and encoded with `tools/encode_demo.swift`; the result is a 124-second, 1600×1000 all-English MP4.
   - Deleted 22 stale `.cover` trace files under the source directories and the `.coverage/` cache (Git-ignored and regenerable).
3. Pitfall: `encode_demo.swift` fails with AVFoundation "Cannot Save (-11823)" when writing directly to an existing path; encoding to a temporary path first and then moving it over works.
4. Confirmed that the project description's "Java/Python standard libraries only" clause applies to the implementation: `model`, `controller`, `cli`, `storage`, `view`, and `main.py` use only the Python standard library. The two non-Python tool scripts (`tools/build_slides.mjs` for the PPTX, `tools/encode_demo.swift` for the MP4) are build/presentation tooling that is deliberately excluded from both the archive whitelist and the submission archive; the four packaged tool scripts use only the standard library.
5. Added bilingual documentation: `README.md` (English, default) with `README.zh-CN.md`, and `deploy_readme.md` (English) with `deploy_readme.zh-CN.md`. Each file links to its counterpart so the language can be switched on GitHub.
6. Pushed commit `7f9745c` ("Regenerate demo transcript and video in English") to `origin/main` and verified that the local and remote HEADs match.

## Final submission checklist

- [x] Full test pass on Python 3.9.6 / 3.12.14 with a real line-coverage report generated
- [x] SRS, current design/API, user/developer manuals, and the requirements-coverage table provided as PDFs
- [x] 6-page presentation PPTX/PDF and the 124-second system demo MP4
- [x] English-only source and demo artifacts; bilingual README and implementation log
- [ ] Check the exact Lecture 04 section structure; confirm the alarm semantics if the instructor requires automatic reminders
- [ ] Fill in member names, roles, and the jointly agreed contribution shares
- [ ] Use the official Honour Declaration to declare AI assistance truthfully, signed by all members
- [ ] Record a presenters-on-camera report of no more than 5 minutes, each member speaking at least 1 minute and meeting the on-camera/student-card requirement
- [ ] Have the team review code and documents, fill in the real `review_status`, and build the final ZIP
- [x] Verify the hosted GitHub Actions CI after pushing (run `35303259313`, Python 3.9/3.11/3.12 all succeeded)

## 2026-10-12: Windows review compatibility

1. Added run_windows.cmd (CRLF) to launch with Python 3.9+ and UTF-8 from the project folder; --check runs tests/coverage and syntax checks. PATH selection preserves the interpreter chosen by a virtual environment or CI.
2. Added Windows-only path validation before filesystem access for reserved devices, alternate data streams, illegal/trailing characters and device/extended namespaces. Documented single-quoted backslash paths, forward slashes and Unicode file portability.
3. Fixed subprocess-test encoding assumptions and added checks for CP1252/CP936 output, Unicode/spaced source and data directories, CRLF input/files, exact drive/UNC arguments and native CMD startup. Updated packaging to include the launcher, .gitattributes and CI workflow.
4. Configured Windows/macOS/Ubuntu CI for Python 3.9/3.11/3.12. Local macOS 3.9.6 and 3.12.14 pass the 133-test suite with zero failures/errors and one native-Windows test skip. The CP1252 default simulation also passes the suite. Compilation and diff checks pass; model coverage is 436/440 (99.09%). Actual Windows and hosted CI are pending; PDF/PPTX exports and team approvals remain unchanged.
