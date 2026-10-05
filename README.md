# COMP3211 Personal Information Management System

**English** | [中文](README.zh-CN.md)

A command-line personal information management system built on the Python standard library. It supports text notes, tasks, events, and contacts, together with type/field search, editing, printing, deletion, and `.pim` save/load.

## Run and verify

Python 3.9+ is supported, with no third-party runtime dependencies. This revision was validated on Windows with Python 3.12.10 and 3.12.14; earlier revisions were validated on macOS with Python 3.9.6 and 3.12.14.

Current local status (5 October 2026 code-review fixes): 83 automated tests collected, 81 passed and 2 platform-dependent tests skipped on both Windows interpreters, with no failures or errors. Fresh model line coverage is 434/438 (99.09%, including unexecuted lines); coverage_report.txt records skipped tests separately. PDF/PPTX artifacts remain the earlier authoring snapshot; regenerate them before final submission as described in the developer manual. The existing CI matrix covers Ubuntu with Python 3.9/3.11/3.12; hosted CI was not run during this review.

```bash
python3 main.py
python3 -m unittest discover -v
python3 tools/check_coverage.py
```

On Windows with the Python launcher installed, use `py -3` in place of `python3`.

```text
add text "Buy milk"
add task "Submit report" --deadline 2026-11-19 20:00
add event "Group meeting" --start 2026-10-12 09:00 --alarm 2026-10-12 08:30
add contact --name "Zhang San" --address "Hung Hom, Hong Kong" --mobile "+852 61234567"
search text contains "Buy milk"
search type = task && deadline < 2026-12-01
edit 2 --deadline 2026-11-20 12:00
print all
save records.pim
load records.pim
exit
```

Enter `help` for the full syntax. When overwriting a file, loading over unsaved data, or exiting with unsaved changes, confirm with `y` at the prompt. `alarm` is a stored, searchable time field; this version does not raise system notifications. Times have minute precision and carry no time zone; a bare date means midnight.

## Architecture and reliability

The `model` package concentrates all business models, ID management, field validation, and the search AST, independent of IO. `cli` handles commands and interaction, `storage` handles strict JSON and atomic saves, and `view` handles formatting; `controller` remains as a compatibility import entry point.

Unknown or duplicate fields, invalid IDs, malformed dates, and corrupted files all raise explicit errors. An edit takes effect only after full validation; a failed save preserves the previous file, and a failed load preserves the current data. See the user manual for limits and usage details.

## Documentation and submission status

- [SRS](docs/SRS.md), [current design/API](docs/design.md), [user manual](docs/user_manual.md), [developer manual](docs/dev_manual.md)
- [US-to-SRS coverage table](requirements_coverage.md), [model line-coverage PDF](coverage_report.pdf) and [reproducible text report](coverage_report.txt)
- [Grading acceptance checklist](docs/submission_checklist.md), [AI usage record](docs/ai_usage.md), [implementation log](deploy_readme.md) ([中文](deploy_readme.zh-CN.md))
- [Presentation script and pending team assignments](docs/presentation_script.md)
- [PDF documents](output/pdf/), [presentation PDF](output/presentation/PIM_presentation.pdf) and [editable PPTX](output/presentation/PIM_presentation.pptx)
- [2 min 04 s recorded CLI-output demo](output/demo/system_demo.mp4) (no narration; not the presenters-on-camera recording)

The earlier [system_design.md](docs/system_design.md) is a historical plan; the current implementation is defined by `docs/design.md`. The coverage tool counts unexecuted lines, so the older trace summary of "100%" must not be read as a code-quality claim.

Run `python3 tools/check_submission.py` to check submission completeness. Member identities, contribution shares, the Lecture 04 structure check, the official Honour Declaration, and the presenters-on-camera recording are still to be completed by the team. All AI-assisted content must be declared truthfully; passing tests does not guarantee a course grade.

To build a reviewable but non-final archive: `python3 tools/package_submission.py --draft`. Output lands in `submission/` and includes the list of open items; without `--draft` it refuses to package an incomplete final submission. Record real human verification results as described in `docs/review_status.example.json`; do not set fields to true without checking them.
