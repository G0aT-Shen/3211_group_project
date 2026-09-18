# Submission and Marking Checklist

Course source: Project+Description+-+2026.pdf, Deliverables 1-5 and Appendix A/B. This checklist maps evidence to the rubric and explicitly preserves unresolved human work.

## Deliverable 1: SRS (6 points)

docs/SRS.md and its PDF contain scoped, numbered functional/nonfunctional requirements, interface semantics and acceptance criteria. Validity/consistency are supported by US mapping and tests. TO BE FILLED BY TEAM: compare chapter headings with Lecture 04; approve alarm interpretation and identify members. These review dependencies prevent calling the document instructor-approved.

## Deliverable 2: design (5 points)

docs/design.md and its PDF explain MVC choices, domain encapsulation, complexity, error boundaries, public/protected API signatures/exceptions, architecture/class relationships and a combined search-and-update sequence. Verify the rendered diagrams and current API appendix after future changes. Original system_design.md is preserved as historical context.

## Deliverable 3: implementation (6 points)

Source includes the complete standard-library CLI and independent model. Developer manual specifies macOS, tested Python versions, IDE, compile/run/pdb commands. User manual covers grammar, output interpretation, invalid inputs and persistence. Root requirements_coverage.md maps US and SRS requirements; PDF export is included. The system-in-use video must be MP4 and at most 4 minutes. A reproducible demo script is provided; inspect its actual recording before submitting.

## Deliverable 4: unit tests (4 points)

unittest tests describe behaviors and assert expected outcomes; regression and integration checks supplement model units. coverage_report.txt is at the source root and counts executed/all executable model lines with standard-library trace. High coverage is evidence of execution, not a guarantee of correctness. Both Python 3.9.6 and 3.12.14 were tested locally; hosted CI results remain separate.

## Deliverable 5: presentation (4 points)

Slides cover three requirements (creation, criterion definition, searching), design and a concrete testing/API lesson. The script offers 3- and 4-member schedules within 5 minutes and at least 1 minute each. TO BE FILLED BY TEAM: names, assignments and actual presentation recording. Each speaker must show face/student ID at the start and keep their face visible while speaking. No generated avatar or synthetic identity substitutes for this recording.

## Declaration and packaging

TO BE FILLED BY TEAM: obtain and complete the official Honour Declaration with truthful AI disclosure and agreed contribution percentages. Put it at the ZIP root. All required documents must be DOC/DOCX/PDF unless otherwise allowed. Copy completed official declaration to submission_inputs/Honour Declaration.pdf and the real presentation recording to submission_inputs/presentation_recording.mp4. These local personal materials are excluded from Git.

The final ZIP deadline is 20 November 2026, 20:00. Run tools/check_submission.py before tools/package_submission.py. The package builder refuses incomplete final submissions. It excludes personal working .pim data, caches and Git metadata. No score is guaranteed; the group must review quality and make truthful declarations.
