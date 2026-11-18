# COMP3211 Personal Information Management System

A Python command-line application for notes, tasks, events and contacts. It supports field edits, type/text/time search with Boolean expressions, printing, deletion and complete .pim save/load.

Group: Shen Hanyang (24126376d, leader), Cui Ziqian (24104368d), Yue Nuting (24113439d).

## Run and verify
Python 3.9+; standard library only. No pip installation is needed. Run from the extracted project folder:
```bash
python3 main.py
python3 -m unittest discover -v
python3 tools/check_coverage.py
```
On Windows, use `run_windows.cmd` to start the application or `run_windows.cmd --check` for tests, coverage and syntax checks. Direct commands can use `py -3 -X utf8` instead of `python3`.

Enter `help` at `pim>` for syntax. Example:
```text
add task "Submit report" --deadline 2026-11-19 20:00
search type = task && deadline < 2026-12-01
edit 1 --deadline 2026-11-20 12:00
print all
save records.pim
exit
```
Data stays in memory until saved. Loading replaces the active collection after validation and any required confirmation. Quote multiword values and Windows backslash paths. Event alarms are stored and searchable timestamps.

Verified on macOS with Python 3.9.6 and 3.12.14, 17 November 2026: **120 tests, 119 passed, one native Windows CMD test skipped, zero failures/errors**. Model line coverage on Python 3.12.14: **436/440 (99.09%)**. Native Windows execution is unverified for this revision. The former 133-test count included 13 tests for authoring helpers now kept outside the submission.

## Documents and media
- [SRS](output/pdf/SRS.pdf), [design and API contracts](output/pdf/design.pdf), [developer manual](output/pdf/dev_manual.pdf), [user manual](output/pdf/user_manual.pdf).
- [Requirements coverage](requirements_coverage.pdf), [model coverage PDF](coverage_report.pdf), [reproducible text report](coverage_report.txt).
- [Presentation slides](output/presentation/PIM_presentation.pdf), [system-use demo](output/demo/system_demo.mp4).
- [GenAI assistance disclosure](output/pdf/ai_usage.pdf). Code, tests, documents and presentation materials received assistance from Codex, Claude Code and DeepSeek Harness as described there.

For the final ZIP, add the completed official **Honour Declaration** at the ZIP root and the separate **group presentation MP4**. These two files are not present in this project folder. The group presentation must be at most five minutes, with each member presenting for at least one minute, showing their face and student ID at the start and keeping their face visible while speaking. Agree and record contribution percentages in the official form.

Keep `model/`, `cli/`, `controller/`, `storage/`, `view/`, `tests/`, `tools/check_coverage.py`, `main.py` and the Windows launcher together. Exclude `.git/`, caches and temporary personal .pim files when creating the ZIP.
