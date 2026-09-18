# Software Requirements Specification

COMP3211 Personal Information Management System | Version 0.2 | 18 September 2026

## 1. Preface

Audience: course assessors, the development group and future maintainers. Source of mandatory scope: Course Project Description, Fall 2026, Appendix B (US1-US11), and Deliverables 1-4. Requirements below distinguish course functionality from team-selected interaction and quality rules. Group members, contribution percentages and approval date: TO BE FILLED BY TEAM.

Lecture 04 is not available in the project folder. The chapter structure below follows Preface, Introduction, Glossary, User requirements, System architecture and System requirements. The team must check the exact lecture structure before submission. System models, System evolution, Appendix and Index chapters are deliberately omitted as requested by the course description.

## 2. Introduction

The system manages personal notes, tasks, events and contacts through a local command line. A user starts one process, creates records, searches or edits them, and saves the collection for a later session. The system needs neither a network connection nor a database server. The product is for a single user and one active collection per process.

Implementation language: Python, using only its standard library. The project supports Python 3.9 or later; verified development environments are macOS with CPython 3.9.6 and 3.12.14. Python 3.11 is a team target and CI matrix entry, not a version mandated by the course PDF. No package installation is required to run the application or tests.

Scope excludes accounts, GUI, cloud synchronization, background processes and OS notification delivery. An event stores an alarm time that users can print and search. Automatic reminders are not promised by this version. This interpretation follows US4's request to create events with descriptions, starting times and alarms; obtain instructor clarification if notification delivery is expected.

## 3. Glossary

PIR: personal information record, identified by a positive integer within a saved collection.

PIM: personal information management system. Criterion: a Boolean expression evaluated on a PIR. AST: abstract syntax tree representing a parsed criterion. Dirty state: the active collection has been changed since its last successful save/load. Local time: a datetime without timezone metadata, interpreted consistently in the user's chosen local timezone. Schema version: the format identifier at the root of a .pim JSON document.

## 4. User requirements

UR-01 (US1-US5): Users can create notes, tasks, events and contacts with all required data and identify each saved record.

UR-02 (US6): Users can change any data field on a record without changing its ID or type.

UR-03 (US7): Users can find records using types, text containment, time comparisons, logical conjunction, disjunction and negation.

UR-04 (US8-US9): Users can inspect one or all records and delete a chosen record.

UR-05 (US10-US11): Users can save and restore collections using .pim files.

UR-06 (team quality rule): Invalid commands explain the problem and leave the process usable. Failed edits and failed file operations preserve the previously valid data.

## 5. System architecture

MVC with explicit persistence adapter. The independent model package owns PIR classes, factory/schema validation, collection state/IDs and search criteria. The CLI adapter parses command syntax and dispatches operations. The view formats output. Storage translates validated model snapshots to/from UTF-8 JSON. Main creates the REPL. The model imports no CLI, storage or view modules and performs no input/output.

The controller package is a compatibility facade exporting the model manager/factory. The CLI Repl provides the active controller behavior. This arrangement preserves early project imports while keeping all business rules in model for unit testing. No third-party runtime dependencies are permitted.

## 6. System requirements

### 6.1 Functional requirements

FR-01 (US1): A successful add shall return a unique positive integer ID. IDs shall increase monotonically within a collection and shall not be reused after deletion. A failed add shall not consume an ID.

FR-02 (US2): add text shall require exactly one nonblank text value and preserve its content, including Unicode, spaces inside quotes and leading zeroes.

FR-03 (US3): add task shall require a nonblank description and valid deadline.

FR-04 (US4): add event shall require a nonblank description, starting time and alarm time. Alarm is a stored timestamp. No restriction between alarm and start is imposed because the course does not specify one.

FR-05 (US5): add contact shall require nonblank name, address and mobile strings. Mobile strings shall preserve international prefixes, punctuation and leading zeroes. Phone-number regional validation is outside scope.

FR-06 (US6): edit shall validate all provided fields, then replace the selected record atomically, preserving ID/type. Missing records, unknown fields, repeated fields, incompatible fields or invalid values shall fail without modifying any record.

FR-07 (US7): search shall support type = and != for text/task/event/contact. Text fields shall support contains, = and != using Unicode casefold. Time fields shall support <, >, = and the extensions <=, >=, != using parsed local datetimes.

FR-08 (US7): Boolean precedence shall be ! then && then ||. Parentheses shall override precedence. A comparison on a field absent from a record shall be False, including !=. Logical NOT shall negate that result normally. Results shall be ordered by ascending ID. Invalid criteria shall be rejected even when the collection is empty.

FR-09 (US8): print <id> shall show the record ID, type and every field. print and print all shall show all records ordered by ID. An empty collection/search shall display a no-match message.

FR-10 (US9): delete <id> shall delete only that record. A nonexistent ID shall raise a friendly error and preserve the collection.

FR-11 (US10): save [file.pim] shall serialize the entire collection with schema_version, next_id and pirs. Omitted filename shall mean pim.pim in the process working directory. Saving over an existing file shall require explicit confirmation. A failed write/replacement shall preserve the old file.

FR-12 (US11): load <file.pim> shall fully decode and validate a file before replacing the active collection. It shall restore types, fields, IDs and next_id. Unsaved edits shall require confirmation before replacement. Invalid input files shall leave the current collection intact.

FR-13: help shall describe command syntax, search syntax and persistence warnings. exit/quit shall confirm before discarding unsaved modifications. EOF shall end the process and warn if modifications are unsaved. Ctrl-C at the input prompt shall cancel the current input and return to the prompt.

### 6.2 Data and interface rules

DR-01: Input timestamps shall be YYYY-MM-DD, YYYY-MM-DD HH:MM, YYYY-MM-DDTHH:MM or persisted YYYY-MM-DDTHH:MM:00. A date alone means midnight. Seconds other than zero, fractional seconds, timezone offsets, impossible calendar dates and non-zero-padded dates shall be rejected. Display precision is minutes; persisted precision is seconds with :00.

DR-02: Only files whose final suffix is .pim (case-insensitive) shall be saved/loaded. JSON must be UTF-8, without duplicate keys or nonfinite numbers. Symlink targets are rejected. File size shall not exceed 10 MiB. The root keys shall be exactly schema_version, next_id, pirs; schema_version shall be integer 1 (not Boolean). next_id shall exceed every existing ID and be at least 1. All record IDs shall be distinct positive integers. Unknown fields shall be rejected.

DR-03: Invalid or missing next_id shall be rejected rather than reconstructed. Reconstructing it from current records could reuse previously deleted IDs. Load is replacement, not merging. Two processes writing the same path are not synchronized; simultaneous writers are outside scope.

IR-01: Command names, type names and option names are case-insensitive. Text data preserves case. Search uses English field names, with start mapping to start_time. Multiword values require quotes. Backslashes/quotes follow POSIX shlex rules. Errors begin with 错误. IDs are positive ASCII decimal strings up to 100 digits at the CLI boundary.

### 6.3 Quality requirements and acceptance

NFR-01: All production imports shall be Python standard library or project-local modules. Automated import checks shall detect an added external dependency.

NFR-02: All business-state and search rules shall reside under model, without console or file IO. Records and returned collections shall protect state from ordinary direct mutation.

NFR-03: Expected invalid-input conditions shall produce domain errors rather than a traceback. Commands are limited to 16,384 characters, criteria to 8,192 characters and nested search operators/parentheses to 64 levels. Files are limited as in DR-02. No platform-independent latency claim is made.

NFR-04: Every unit test shall state the behavior it exercises and assert observable expected results. All tests shall execute automatically with unittest. Regression cases shall include malformed commands, failed atomic edits, bad JSON/schema and disk replacement failure.

NFR-05: The root coverage report shall state executed and total executable model lines, include unexecuted lines in its denominator and identify excluded packages. Target model line coverage is at least 95%; this is a project quality goal, not an instructor-specified threshold. High coverage shall not substitute for correctness checks.

NFR-06: Developer/user manuals, API contracts, sequence/architecture/component diagrams and the root requirements coverage table shall match the implemented version. The table shall map both US and SRS requirements to tests. Official submission documents shall be PDF, DOC or DOCX.

### 6.4 Acceptance examples

Create all four types, edit a task deadline, search type = task && deadline < 2027-01-01, print the selected ID, delete it, save, restart, and load. Confirm field values and the next allocated ID. Repeat with print abc, delete without an ID, an unknown edit field, an invalid date and a corrupt JSON file. Every invalid operation must preserve prior data and allow the next valid command. Automated coverage: tests/test_acceptance.py and tests/test_quality.py.

### 6.5 Open approvals

TO BE FILLED BY TEAM: member names and responsibilities; contribution percentages agreed by all members; Lecture 04 chapter-structure comparison; instructor confirmation of alarm-field interpretation if needed. These are not represented as completed approvals.
