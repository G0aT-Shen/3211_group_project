# Requirements Coverage Report

Version 0.2, Revision 2 | 5 October 2026. Source: original Course Project Description, Appendix B, and docs/SRS.md. All 11 course user stories have implementation and automated acceptance evidence. This is requirement coverage, not a claim of 100% line coverage or a guaranteed grade. Open human approval/submission items are identified separately.

Current verification: 89 tests passed with no failures, errors or skips on macOS with Python 3.9.6 and 3.12.14. The checked-in model line report was regenerated with Python 3.12.14: 439/443 executable lines (99.10%). Production and tool syntax compilation passed on both interpreters. This revision has not been run on Windows or hosted CI; earlier Windows results do not establish the status of this revision.

| Course story | SRS requirements | Implementation evidence | Test evidence | Status |
|---|---|---|---|---|
| US1 common collection/types | UR-01, FR-01 | model.manager, model.factory | ModelContractTests.test_manager_snapshot_and_id_integrity | Implemented |
| US2 plain texts | FR-02 | model.text_pir | ModelContractTests.test_every_record_round_trips_and_prints_all_fields | Implemented |
| US3 tasks/deadlines | FR-03 | model.task_pir | ModelTests.test_task_and_event_dates; ModelContractTests.test_dates_are_strict_and_minute_precision | Implemented |
| US4 events/start/alarm | FR-04 | model.event_pir | ModelContractTests.test_getters; SearchContractTests.test_time_operators_on_every_time_field; AcceptanceTests.test_real_process_all_user_stories | Implemented; alarm is the stored time field specified in US7 |
| US5 contacts | FR-05 | model.contact_pir | ModelContractTests.test_getters | Implemented |
| US6 edit fields | UR-02, FR-06 | model.manager.edit_pir | ModelContractTests.test_all_fields_edit_and_failed_edits_are_atomic | Implemented |
| US7 criteria/search | UR-03, FR-07/08 | model.search | SearchContractTests (all methods); SearchQuotingTests (all methods); ControllerTests.test_list_and_search_sort_shuffled_initial_ids | Implemented |
| US8 print one/all | UR-04, FR-09 | view.printer, cli.repl | ModelContractTests.test_every_record_round_trips_and_prints_all_fields; AcceptanceTests.test_real_process_all_user_stories | Implemented |
| US9 delete | FR-10 | model.manager.delete_pir | ControllerTests.test_crud_and_monotonic_ids; test_missing_record_raises (remaining data and IDs preserved) | Implemented |
| US10 .pim save | UR-05, FR-11 | storage.Storage.save | AcceptanceTests.test_real_process_all_user_stories (exact four-type disk snapshot); StorageContractTests.test_failure_does_not_truncate_existing_file | Implemented |
| US11 .pim load | FR-12 | storage.Storage.load | AcceptanceTests.test_real_process_all_user_stories (new process restores exact fields and ID allocation); ReplContractTests.test_bad_load_keeps_active_model | Implemented |

## Course code and test constraints

| Course requirement | Current evidence | Status |
|---|---|---|
| Command-line-based PIM; no GUI required | main.py starts cli.Repl; AcceptanceTests runs main.py in separate processes | Implemented |
| Python/Java; standard libraries only | Python implementation; AcceptanceTests.test_production_imports_are_standard_library_or_project | Implemented |
| All model code in a separate model package; other components identifiable | model owns records, validation, collection and search; cli, storage and view are separate; AcceptanceTests.test_model_has_no_io_or_outer_layer_imports | Implemented |
| Automatically executable model unit tests with behavior descriptions and expected-result assertions | unittest discovery; ModelTests, ModelContractTests, SearchContractTests and ControllerTests describe and assert domain behavior | Implemented |
| Model line coverage in a separate file at the source root | coverage_report.txt and coverage_report.pdf; tools/check_coverage.py counts executed and missed executable lines | Implemented |
| Table at source root mapping course stories and SRS requirements to implemented/not implemented status | This report and requirements_coverage.pdf | Implemented |

## Remaining SRS requirements

| Requirement | Evidence / acceptance check | Status |
|---|---|---|
| UR-06, NFR-03 errors/limits | CommandContractTests.test_invalid_commands; SearchContractTests.test_invalid_search_and_resource_limits; RegressionTests.test_invalid_ids_do_not_end_session; ConsoleEncodingTests.test_undecodable_input_is_rejected_without_losing_session | Implemented |
| FR-13 help/exit/EOF/Ctrl-C | ReplContractTests.test_loop_eof_interrupt_and_domain_errors; test_confirmation_input_and_eof; test_cancelled_save_load_exit_keep_state | Implemented |
| DR-01 datetime rules | ModelContractTests.test_dates_are_strict_and_minute_precision; ModelTests.test_timestamp_display_keeps_four_digit_years_at_calendar_boundaries; SearchContractTests.test_time_operators_on_every_time_field | Implemented |
| DR-02 strict .pim schema/limits | ModelContractTests.test_strict_file_schema; StorageContractTests.test_invalid_files_and_extensions; test_size_limits_and_serialization_failure | Implemented |
| DR-03 next_id/replacement | ModelContractTests.test_manager_snapshot_and_id_integrity; test_strict_file_schema; ReplContractTests.test_cancelled_save_load_exit_keep_state | Implemented |
| IR-01 syntax/case/IDs | CommandContractTests (all methods); SearchContractTests.test_contains_on_all_text_fields; SearchQuotingTests.test_escaped_and_concatenated_words_match_command_text | Implemented |
| NFR-01 stdlib only | AcceptanceTests.test_production_imports_are_standard_library_or_project | Implemented |
| NFR-02 model separation | AcceptanceTests.test_model_has_no_io_or_outer_layer_imports; ModelContractTests.test_model_is_abstract_and_records_are_immutable; ModelTests.test_record_dictionaries_cannot_bypass_validation_or_change_ids | Implemented |
| NFR-04 automated tests | python3 -m unittest discover -v; behavior docstrings and specific exception assertions | Implemented |
| NFR-05 model line coverage | tools/check_coverage.py; root summary and .coverage/model.*.cover missed-line details; 99.10% exceeds the team-selected 95% target | Implemented |
| NFR-06 matching documents | Updated SRS, design/API contracts, manuals, this table and PDF exports describe the current code; final human review and presentation exports are separate release work | Code documentation updated; final team review pending |

## Qualification

UR-04/05 span multiple course stories, listed in their first applicable row. FR-07 and FR-08 are both covered by the search test class. Tests/test_quality.py owns the named ContractTests; tests/test_acceptance.py owns AcceptanceTests. The report does not claim a guaranteed mark or approval from the instructor.

Alarm interpretation follows both US4 and US7: US4 requires the event field, and US7 explicitly refers to a time stored in an alarm. The original description does not require OS notification delivery, a background scheduler or an alarm/start ordering rule.

Open non-code requirements: final team review of Lecture 04 structure and deliverables, group/member fields, official Honour Declaration and real group presentation recording. The source PDF requests documents in DOC/DOCX/PDF, so PDF exports accompany these Markdown source files. Unit tests and coverage do not replace those human deliverables.
