# GenAI Assistance Record

This is supporting evidence for the group's official Honour Declaration. It is not the official form and contains no signatures or invented contributions.

## Assistance supplied

Codex helped create/revise the Python model, command/search parser, CLI, storage adapter, tests, coverage generator and submission tools. It also drafted the README, SRS, design/API explanations, manuals, requirements mapping, presentation material and demonstration script. The original course PDF is instructor-provided. Early planning files were already present and require the group's own provenance confirmation.

## Review and correction history

The initial implementation passed 12 tests but missed invalid ID crashes, silent unknown edits and multiword search quotation handling. The initial trace command reported only executed lines, producing a misleading 100% summary. Those claims were corrected by regression tests and a new report that counts missed executable lines. The improved suite covers strict schemas, failed disk replacement and cancelled data-loss confirmations. Members must independently review the supplied code and understand the design before presenting.

On 1 October 2026, Codex assisted with a full code review and fixes for command-time interruption, ID range consistency/exhaustion, regular-file loading, incomplete authoring-tool packaging and malformed MP4 nesting. Regression tests first reproduced the failures. The resulting 73-test suite passed locally on Python 3.9.6 and 3.12.14, and an extracted draft archive passed the same suite. Fresh model line coverage measured 436/438 (99.54%). Human deliverables and approvals remain the team's responsibility; the earlier PDF/PPTX authoring snapshot was not regenerated in this code-fix pass.

On 5 October 2026, Codex reviewed the command/search, model/storage and verification tooling. Fixes preserve sessions when redirected output cannot encode Unicode, allow searching single-quoted paths ending in a backslash, correct coverage selection and synthetic-line counting, and separate Windows symlink permissions from storage validation. Added regression tests reproduced the defects before the fixes. Windows Python 3.12.10 and 3.12.14 each ran 83 tests: 81 passed, 2 platform-dependent tests skipped, with no failures or errors. Model line coverage measured 434/438 (99.09%). Python compilation and slide-builder syntax checks passed. The existing Ubuntu CI matrix was not changed, and hosted CI was not run during this review. The text coverage report and Markdown manuals were updated; PDF/PPTX artifacts and human approvals were not regenerated or changed.

Later on 5 October 2026, Codex compared the original course stories and code/test constraints against the source and strengthened the implementation evidence. It removed writable instance dictionaries from immutable records, made timestamp display independent of platform year padding, and aligned search literals with command shell escapes and concatenated quotes. Regression tests reproduced the dictionary mutation and search defects before the fixes. Existing edit, deletion, Unicode search and sorting assertions were strengthened, and the CLI acceptance workflow now validates exact four-type disk snapshots and restoration in a new process. On macOS, Python 3.9.6 and 3.12.14 each passed all 88 tests with no failures, errors or skips; syntax compilation passed on both. The Python 3.12.14 model line report was regenerated at 439/443 (99.10%). The requirements matrix and documentation PDFs were refreshed. The original US7 describes alarm as a stored time field; no active notification feature was added. Windows, hosted CI, presentation exports and human approvals were not performed for this revision.

## Information to transfer into the official form

TO BE FILLED BY TEAM: member names/IDs, AI tools used by each member, dates and assisted deliverables, individual contributions agreed by the entire group, signatures and required declaration wording. Use the official course/university form from Canvas. Do not substitute this note for that form. Do not upload student ID images to a public repository.
