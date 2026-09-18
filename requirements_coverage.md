# Requirements Coverage Report

Version 0.2 | 18 September 2026. Source: original Course Project Description, Appendix B, and docs/SRS.md. Implementation status below refers to tested code; open human approval/submission items are identified separately.

| Course story | SRS requirements | Implementation evidence | Test evidence | Status |
|---|---|---|---|---|
| US1 common collection/types | UR-01, FR-01 | model.manager, model.factory | ModelContractTests.test_manager_snapshot_and_id_integrity | Implemented |
| US2 plain texts | FR-02 | model.text_pir | ModelContractTests.test_every_record_round_trips_and_prints_all_fields | Implemented |
| US3 tasks/deadlines | FR-03 | model.task_pir | ModelContractTests.test_dates_are_strict_and_minute_precision | Implemented |
| US4 events/start/alarm | FR-04 | model.event_pir | ModelContractTests.test_getters; ReplContractTests.test_full_workflow_and_confirmation | Implemented as stored alarm field |
| US5 contacts | FR-05 | model.contact_pir | ModelContractTests.test_getters | Implemented |
| US6 edit fields | UR-02, FR-06 | model.manager.edit_pir | ModelContractTests.test_all_fields_edit_and_failed_edits_are_atomic | Implemented |
| US7 criteria/search | UR-03, FR-07/08 | model.search | SearchContractTests (all methods); RegressionTests.test_cli_search_preserves_quoted_text | Implemented |
| US8 print one/all | UR-04, FR-09 | view.printer, cli.repl | ModelContractTests.test_every_record_round_trips_and_prints_all_fields; AcceptanceTests.test_real_process_all_user_stories | Implemented |
| US9 delete | FR-10 | model.manager.delete_pir | ControllerTests.test_crud_and_monotonic_ids | Implemented |
| US10 .pim save | UR-05, FR-11 | storage.Storage.save | StorageContractTests.test_failure_does_not_truncate_existing_file | Implemented |
| US11 .pim load | FR-12 | storage.Storage.load | StorageContractTests.test_all_types_and_empty_collection_roundtrip; ReplContractTests.test_bad_load_keeps_active_model | Implemented |

## Remaining SRS requirements

| Requirement | Evidence / acceptance check | Status |
|---|---|---|
| UR-06, NFR-03 errors/limits | CommandContractTests.test_invalid_commands; SearchContractTests.test_invalid_search_and_resource_limits; RegressionTests.test_invalid_ids_do_not_end_session | Implemented |
| FR-13 help/exit/EOF/Ctrl-C | ReplContractTests.test_loop_eof_interrupt_and_domain_errors; test_confirmation_input_and_eof; test_cancelled_save_load_exit_keep_state | Implemented |
| DR-01 datetime rules | ModelContractTests.test_dates_are_strict_and_minute_precision; SearchContractTests.test_time_operators_on_every_time_field | Implemented |
| DR-02 strict .pim schema/limits | ModelContractTests.test_strict_file_schema; StorageContractTests.test_invalid_files_and_extensions; test_size_limits_and_serialization_failure | Implemented |
| DR-03 next_id/replacement | ModelContractTests.test_manager_snapshot_and_id_integrity; test_strict_file_schema; ReplContractTests.test_cancelled_save_load_exit_keep_state | Implemented |
| IR-01 syntax/case/IDs | CommandContractTests (all methods); SearchContractTests.test_contains_on_all_text_fields | Implemented |
| NFR-01 stdlib only | AcceptanceTests.test_production_imports_are_standard_library_or_project | Implemented |
| NFR-02 model separation | AcceptanceTests.test_model_has_no_io_or_outer_layer_imports; ModelContractTests.test_model_is_abstract_and_records_are_immutable | Implemented |
| NFR-04 automated tests | python3 -m unittest discover -v; behavior docstrings and specific exception assertions | Implemented |
| NFR-05 model line coverage | python3 tools/check_coverage.py; root coverage_report.txt with missed lines included | Implemented |
| NFR-06 matching documents | docs/design.md, manuals, this table and PDF exports; lecture chapter verification remains open | Partially complete pending team approval |

## Qualification

UR-04/05 span multiple course stories, listed in their first applicable row. FR-07 and FR-08 are both covered by the search test class. Tests/test_quality.py owns the named ContractTests; tests/test_acceptance.py owns AcceptanceTests. The report does not claim a guaranteed mark or approval from the instructor.

Open non-code requirements: Lecture 04 structure verification, group/member fields, official Honour Declaration and real group presentation recording. Alarm behavior is explicitly a stored field; instructor clarification may change that interpretation. The source PDF requests documents in DOC/DOCX/PDF, so PDF exports accompany these Markdown source files.
