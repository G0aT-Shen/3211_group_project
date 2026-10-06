# Submission and Marking Checklist

Course source: Project+Description+-+2026.pdf, Deliverables 1-5 and Appendix A/B. This checklist maps evidence to the rubric and explicitly preserves unresolved human work.

## Deliverable 1: SRS (6 points)

docs/SRS.md and its PDF contain scoped, numbered functional/nonfunctional requirements, interface semantics and acceptance criteria. Validity/consistency are supported by US mapping and tests. The SRS records its Lecture 04 structure alignment; the alarm timestamp interpretation follows US4 and the explicitly stored alarm time in US7. TO BE FILLED BY TEAM: perform the final document review and identify members. Automated code validation does not constitute instructor approval of a document.

## Deliverable 2: design (5 points)

docs/design.md and its PDF explain MVC choices, domain encapsulation, complexity, error boundaries, public/protected API signatures/exceptions, architecture/class relationships and a combined search-and-update sequence. Verify the rendered diagrams and current API appendix after future changes. Original system_design.md is preserved as historical context.

## Deliverable 3: implementation (6 points)

Source includes the complete standard-library CLI and independent model. The current requirements audit covers all US1-US11 and course code/test constraints, including exact four-type persistence across a process restart. Developer manual specifies macOS, tested Python versions, IDE, compile/run/pdb commands. User manual covers grammar, output interpretation, invalid inputs and persistence. Root requirements_coverage.md maps US and SRS requirements; the matching PDF export is included. The system-in-use video must be MP4 and at most 4 minutes. A reproducible demo script is provided; inspect its actual recording before submitting.

## Deliverable 4: unit tests (4 points)

unittest tests describe behaviors and assert expected outcomes; regression and integration checks supplement model units. Current macOS runs passed all 88 tests on Python 3.9.6 and 3.12.14 without skips. coverage_report.txt and its PDF are at the source root and report 439/443 model lines (99.10%) from Python 3.12.14, including missed executable lines. The course does not specify a minimum line-coverage percentage. High coverage is evidence of execution, not a guarantee of correctness. Hosted CI and Windows were not run for the current revision.

## Deliverable 5: presentation (4 points)

Slides cover three requirements (creation, criterion definition, searching), design and a concrete testing/API lesson. The script offers 3- and 4-member schedules within 5 minutes and at least 1 minute each. TO BE FILLED BY TEAM: names, assignments and actual presentation recording. Each speaker must show face/student ID at the start and keep their face visible while speaking. No generated avatar or synthetic identity substitutes for this recording.

## Declaration and packaging

TO BE FILLED BY TEAM: obtain and complete the official Honour Declaration with truthful AI disclosure and agreed contribution percentages. Put it at the ZIP root. All required documents must be DOC/DOCX/PDF unless otherwise allowed. Copy completed official declaration to submission_inputs/Honour Declaration.pdf and the real presentation recording to submission_inputs/presentation_recording.mp4. These local personal materials are excluded from Git.

Deadline: 20 November 2026, 20:00. Run tools/check_submission.py, then tools/package_submission.py. Final packaging rejects missing items and excludes local data, caches and Git.
