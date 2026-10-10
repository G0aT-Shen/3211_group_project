# Software Requirements Specification

COMP3211 Personal Information Management System | Version 0.2, Revision 2 | 5 October 2026

## 1. Preface

### 1.1 Purpose and readership

This Software Requirements Specification (SRS) defines what the COMP3211 Personal Information Management (PIM) system shall provide and the constraints under which it shall operate. It is written for course assessors, users, developers, testers and future maintainers. User requirements describe the services visible to a non-technical user; system requirements refine those services into precise, testable behavior.

The mandatory scope comes from the Fall 2026 Course Project Description, especially Appendix B (US1-US11), Deliverables 1-4 and the standard-library/model-package constraints. The structure follows Lecture 04, slides 31-32: Preface, Introduction, Glossary, User requirements definition, System architecture and System requirements specification. As directed by the project description, chapters for System models, System evolution, Appendices and Index are intentionally omitted.

### 1.2 Version history

| Version | Date | Rationale and summary of changes |
|---|---|---|
| 0.1 | 18 September 2026 | Established the initial scope from US1-US11 and the command-line PIM concept. |
| 0.2 | 18 September 2026 | Added detailed functional, data, interface and quality requirements plus acceptance examples and traceability to tests. |
| 0.2 Revision 1 | 23 September 2026 | Aligned chapter names and preface content with Lecture 04; added requirement rationale, verification methods, stakeholders, interfaces and validation criteria; corrected the documented English error prefix. |
| 0.2 Revision 2 | 5 October 2026 | Rechecked all original course stories and code/test constraints; clarified the US7 basis for alarm semantics and synchronized the implementation evidence. |

### 1.3 Requirement conventions and approval status

Each requirement has a stable identifier. "Shall" denotes a mandatory requirement, "should" denotes a desirable recommendation and "may" denotes an allowed option. Rationale explains why a requirement exists; verification identifies observable evidence. Detailed backward and forward traceability is maintained in the root requirements coverage report.

This revision verifies the document structure against the supplied Lecture 04 slides. Final group approval, member identities, contribution percentages and signatures belong in the official Honour Declaration and are not invented in this SRS.

## 2. Introduction

### 2.1 Need and objectives

Personal notes, tasks, events and contacts are often kept in unrelated places. The PIM system provides one local collection in which a user can create, find, update, inspect, delete, save and restore these records. Its objective is to satisfy US1-US11 through a small, dependable command-line application that can be built, tested and assessed reproducibly.

### 2.2 Product overview

A user starts one process and interacts through text commands. The process maintains one active collection in memory. A user may save the entire collection to a `.pim` file and load it in a later session. The system assigns stable positive integer IDs so records can be selected for printing, editing and deletion.

The product is a standalone local application. It does not integrate with accounts, cloud services, databases, calendars, messaging systems or other network services. Its external interfaces are the terminal for commands and output, and the local filesystem for `.pim` files.

### 2.3 Stakeholders

Primary user: a person managing their own local information. Course assessors evaluate requirements, design, implementation and tests. Developers and testers maintain the implementation and verify behavior. The project group owns final review, presentation and declaration activities.

### 2.4 Scope and constraints

The system includes four PIR types, field-based and compound searching, modification, printing, deletion and file persistence. Accounts, GUI, online synchronization, multi-user access, background services and OS notification delivery are outside scope. An event alarm is a stored, printable and searchable timestamp: US4 requires this event field, and US7 explicitly describes a time stored in an alarm and its comparison operators. Neither story specifies notification delivery.

The implementation language is Python and production code shall use only the Python standard library and project-local modules. The supported interpreter baseline is Python 3.9 or later. The application is designed for one user and one active process writing a given file at a time.

## 3. Glossary

PIM: Personal Information Management system, the product specified by this document.

PIR: Personal information record. A PIR has a type, a positive integer ID and type-specific fields.

Criterion: A Boolean expression evaluated against a PIR during a search.

AST: Abstract syntax tree used to represent a parsed search criterion.

Dirty state: The active collection has changed since its most recent successful save or load.

Local time: A date and time without timezone metadata, interpreted consistently in the user's local context.

Schema version: The integer format identifier stored at the root of a `.pim` document.

Atomic operation: An operation that either completes fully or leaves the previously valid state unchanged.

## 4. User Requirements Definition

The following requirements use user-facing language and identify their source and rationale. Together they cover every story in Appendix B.

UR-01 (US1-US5): The user shall be able to create plain-text notes, tasks with descriptions and deadlines, events with descriptions, starting times and alarms, and contacts with names, addresses and mobile numbers. Each created PIR shall be identifiable. Rationale: the four record types must be managed in one location. Verification: create and print one record of every type.

UR-02 (US6): The user shall be able to change the data fields of an existing PIR without changing its ID or type. Rationale: stored information must remain current while references to the record remain stable. Verification: edit every supported field and print the same ID.

UR-03 (US7): The user shall be able to search by PIR type and field data, including text containment, time comparison and compound conditions using AND, OR and NOT. Rationale: a mixed collection is useful only when relevant records can be found precisely. Verification: execute simple and compound searches and compare the returned IDs with the expected set.

UR-04 (US8-US9): The user shall be able to inspect one PIR or all PIRs and delete a selected PIR. Rationale: users need both visibility and control over their collection. Verification: print one/all records, delete one ID and confirm that other records remain.

UR-05 (US10-US11): The user shall be able to save the active collection to a `.pim` file and restore it in a later session. Rationale: information must survive process termination. Verification: save, restart, load and compare IDs, types and all field values.

UR-06 (project quality rule): Invalid commands or data shall produce an understandable error and leave the application usable. A failed edit, save or load shall preserve the last valid state. Rationale: routine input and file errors must not silently lose or corrupt personal information. Verification: submit malformed commands, invalid dates and damaged files, then perform a valid command and inspect the preserved state.

### 4.1 User-level quality expectations

The application shall run locally without a network connection or third-party runtime package. Commands and output shall be documented in a user manual. Destructive replacement of a file or unsaved collection shall require explicit confirmation. The system should give deterministic results for the same collection and criterion.

## 5. System Architecture

The anticipated architecture is Model-View-Controller (MVC) with an explicit persistence adapter. It separates business rules from terminal interaction and file IO so the model can be unit-tested independently, as required by the project description.

| Component | Responsibility | Dependency and reuse boundary |
|---|---|---|
| `main.py` | Construct and start the command loop. | Depends on the CLI adapter only. |
| `model` | Own PIR types, field validation, IDs, collection state and search criteria. | Depends only on Python standard-library modules; performs no console or file IO. |
| `cli` / `Repl` | Parse commands, coordinate model/storage/view operations and confirmations. | Depends on model, storage and view. It acts as the active controller adapter. |
| `controller` | Preserve the public manager/factory import boundary. | Reuses and re-exports model services; contains no separate business state. |
| `storage` | Translate validated model snapshots to and from strict UTF-8 JSON `.pim` files. | Depends on model and Python filesystem/JSON libraries. |
| `view` | Format records, messages, empty results and errors for the terminal. | Depends on model display contracts only. |

The reused platform components are Python's standard library for dates, regular expressions, shell-like tokenization, JSON and atomic filesystem replacement. No third-party runtime component is part of the product. Detailed class relationships and interaction diagrams belong to the separate design document rather than this SRS.

## 6. System Requirements Specification

### 6.1 Functional requirements

FR-01 (US1): A successful add operation shall return a unique positive integer ID. IDs shall increase monotonically within a collection and shall not be reused after deletion. A failed add shall not consume an ID. Rationale: stable IDs support later operations and persistence. Verification: add, fail an add, delete and add again while checking the allocated IDs.

FR-02 (US2): `add text` shall require exactly one nonblank text value and preserve its content, including Unicode, quoted spaces and leading zeroes. Rationale: note content must not be altered by parsing. Verification: round-trip representative text through creation, printing, save and load.

FR-03 (US3): `add task` shall require a nonblank description and valid deadline. Rationale: both fields define a usable task. Verification: accept a valid task and reject missing, blank or invalid fields without changing the collection.

FR-04 (US4): `add event` shall require a nonblank description, starting time and alarm time. The alarm shall be stored, printed, editable and searchable, consistent with the stored time field in US7. No ordering restriction between alarm and start shall be imposed because Appendix B specifies both fields but no relationship or active notification behavior. Verification: create, edit, search, print and persist events with both timestamps.

FR-05 (US5): `add contact` shall require nonblank name, address and mobile strings. Mobile values shall preserve international prefixes, punctuation and leading zeroes. Rationale: contact data must not be damaged by numeric conversion. Verification: round-trip representative contact values.

FR-06 (US6): `edit` shall validate every supplied field before replacing the selected record and shall preserve its ID and type. A missing record, unknown, repeated or incompatible field, or invalid value shall fail without modifying any field. Rationale: partial edits could leave contradictory data. Verification: test successful edits for every field and multi-field failures that preserve the original record.

FR-07 (US7): Search shall support `type =` for text, task, event and contact; `contains` for every textual field; and `<`, `>` and `=` for deadline, starting time and alarm. It may additionally support `!=`, `<=` and `>=`. Text comparisons shall be case-insensitive using Unicode case folding, while time comparisons shall use parsed datetimes. Verification: compare result IDs for every field/operator category.

FR-08 (US7): Search shall support `!`, `&&`, `||` and parentheses, with precedence `!` then `&&` then `||`. A comparison involving a field absent from a PIR shall be false before logical negation. Results shall be ordered by ascending ID, and an invalid criterion shall be rejected even for an empty collection. Rationale: explicit semantics prevent ambiguous compound searches. Verification: test precedence, parentheses, negation, missing fields and malformed criteria.

FR-09 (US8): `print <id>` shall show the selected record's ID, type and every field. `print` and `print all` shall show all records in ascending ID order. An empty collection or result shall display `No matching PIRs.` Rationale: users must be able to interpret complete stored data and empty results. Verification: capture output for one, many and zero records.

FR-10 (US9): `delete <id>` shall delete only the selected record. A nonexistent ID shall produce an error and preserve the collection. Rationale: deletion must not affect unrelated information. Verification: delete one of several records and attempt deletion of a missing ID.

FR-11 (US10): `save [file.pim]` shall serialize the complete collection, including `schema_version`, `next_id` and every PIR. An omitted filename shall mean `pim.pim` in the process working directory. Overwriting an existing file shall require explicit confirmation. A failed write or replacement shall preserve the old file. Verification: inspect round-trip data, cancelled overwrite behavior and simulated replacement failure.

FR-12 (US11): `load <file.pim>` shall completely decode and validate a file before replacing the active collection. It shall restore types, fields, IDs and `next_id`. Replacing unsaved changes shall require confirmation. Invalid input shall preserve the active collection. Verification: test valid round trips, cancellation and malformed files.

FR-13: `help` shall describe command, search and persistence syntax. `exit` and `quit` shall confirm before discarding unsaved changes. End-of-file shall terminate and warn when changes are unsaved; Ctrl-C at the input prompt shall cancel the current input and return to the prompt. Rationale: lifecycle behavior must be predictable and avoid accidental loss. Verification: exercise each control path with captured input/output.

### 6.2 Data requirements

DR-01: Accepted timestamps shall use `YYYY-MM-DD`, `YYYY-MM-DD HH:MM`, `YYYY-MM-DDTHH:MM` or persisted `YYYY-MM-DDTHH:MM:00`. A date alone shall mean midnight. Nonzero seconds, fractional seconds, timezone offsets, impossible dates and non-zero-padded dates shall be rejected. Display precision shall be minutes; persisted precision shall include `:00` seconds. Verification: boundary tests for valid, invalid and leap-day timestamps.

DR-02: Only files with a final `.pim` suffix, case-insensitively, shall be saved or loaded. A file shall be UTF-8 JSON, contain no duplicate keys or nonfinite numbers and be no larger than 10 MiB. Symbolic-link paths shall be rejected. The root keys shall be exactly `schema_version`, `next_id` and `pirs`; `schema_version` shall be integer 1, not Boolean. PIR IDs shall be distinct positive integers, and unknown fields shall be rejected. Verification: load valid and systematically malformed files and inspect resulting state.

DR-03: `next_id` shall be a positive integer greater than every existing ID. A missing or invalid value shall be rejected rather than reconstructed because reconstruction could reuse a deleted ID. Loading shall replace rather than merge collections. Simultaneous writers to one file are outside scope. Verification: test deleted-ID persistence, invalid metadata and replacement semantics.

### 6.3 External interface requirements

IR-01: The terminal interface shall accept case-insensitive command names, type names and option names while preserving the case of stored text. Search shall use English field names, with `start` as an alias for `start_time`. Multiword values shall use shell-style quoting. IDs at the command boundary shall be positive ASCII decimal strings of at most 100 digits. Expected domain errors shall begin with `Error:` and shall not display a traceback. The filesystem interface shall read and write complete `.pim` collections; save shall use a temporary file followed by atomic replacement, and the parent directory shall already exist. Verification: parser, real-process and storage tests shall cover aliases, quoting, invalid input and filesystem failures.

### 6.4 Non-functional requirements

NFR-01 - Portability and dependency constraint: Production imports shall be Python standard-library or project-local modules. The program shall run on Python 3.9 or later without installing runtime packages. Verification: automated import inspection, syntax compilation and tests on supported Python versions.

NFR-02 - Modularity and testability: All business state, validation and search rules shall reside in the `model` package without console or file IO. Records and returned collections shall resist ordinary direct mutation. Verification: architecture import tests and model immutability tests.

NFR-03 - Reliability and bounded input: Expected invalid input shall produce a domain error rather than a traceback. Commands shall be limited to 16,384 characters, search criteria to 8,192 characters, nested Boolean/parenthesis levels to 64 and files to 10 MiB. Verification: automated boundary and regression tests.

NFR-04 - Automated tests: Unit tests shall state the behavior exercised and assert observable expected results. All tests shall be automatically executable using `unittest`. Regression coverage shall include malformed commands, atomic edit failure, invalid JSON/schema and disk replacement failure. Verification: run the complete test suite from the repository root.

NFR-05 - Coverage evidence: The root coverage report shall state executed and total executable model lines, include missed executable lines in its denominator and identify excluded packages. The project quality target is at least 95% model line coverage; this target is team-selected rather than instructor-mandated. Verification: regenerate and inspect `coverage_report.txt` and its PDF export.

NFR-06 - Documentation consistency: Developer and user manuals, API contracts, architecture/component/interaction diagrams and the root requirements coverage table shall describe the released implementation. The coverage table shall map Appendix B stories and SRS requirement IDs to implementation and test evidence. Required submission documents shall be delivered as PDF, DOC or DOCX. Verification: release review plus the submission checker.

### 6.5 Acceptance and validation

The primary acceptance scenario shall create all four PIR types, edit a task deadline, search using `type = task && deadline < 2027-01-01`, print the selected ID, delete it, save, restart and load. The restored records and next allocated ID shall match the pre-save state. Negative scenarios shall include `print abc`, delete without an ID, an unknown edit field, an invalid date and corrupt JSON. Every invalid operation shall preserve prior valid data and allow the next valid command.

Requirements validation uses the five checks from Lecture 04. Validity is supported by direct mapping to US1-US11. Consistency is checked through shared field schemas and common datetime/storage rules. Completeness is checked by the requirements coverage table. Realism is supported by a standard-library implementation and executable acceptance scenario. Verifiability is provided by observable acceptance criteria and automated tests. Manual review remains necessary for usability, document accuracy and presentation readiness.

The root `requirements_coverage.md` provides the detailed traceability matrix from course stories and SRS requirements to code and tests. `tests/test_acceptance.py` and `tests/test_quality.py` automate the main positive and negative acceptance scenarios.
