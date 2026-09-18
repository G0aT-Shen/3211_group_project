# Presentation and Demo Script

## Five-minute group presentation

Slide 1: project title; presenters TO BE FILLED BY TEAM. Each member must show face and student ID when beginning their section. Keep the current speaker's face continuously visible. Total planned speaking time: 4 minutes 40 seconds, leaving 20 seconds for transitions. Rehearse with a timer.

For 4 members: A covers slides 1-2 for 70 seconds; B covers slide 3 for 70 seconds; C covers slides 4-5 for 70 seconds; D covers slide 6 for 70 seconds. For 3 members: A covers slides 1-2 for 90 seconds; B covers slides 3-4 for 95 seconds; C covers slides 5-6 for 95 seconds. All durations exceed the one-minute requirement.

Slide 1 opening: This is a local CLI for notes, tasks, events and contacts. We chose a small standard-library product so setup and testing remain reproducible. Insert real team names before recording.

Slide 2 creation requirement: Show add task with a description/deadline. FR-03 specifies required fields and FR-01 assigns an ID only on success. Explain how a bad date leaves state unchanged. This is verifiable user behavior, not just an API name.

Slide 3 criterion definition/search: Explain type = task && deadline < 2027-01-01. A criterion is parsed once and evaluated on each record. Then explain parentheses and ! > && > ||, plus field absence semantics. Multiword string quotes must survive command parsing. Present FR-07/08 as the second/third required requirement topics.

Slide 4 architecture: Explain model ownership of immutable records, factory, collection and search AST. CLI is the controller adapter, storage handles IO and view formats results. The model has no input/output imports. This makes unit tests independent of files and prompts.

Slide 5 search/update: Walk through user command, parser, search AST, manager result, chosen ID, factory validation and atomic replacement. If one field fails, the old record remains. Connect API design to the user's confidence when editing records.

Slide 6 lesson: The first tests passed while print abc still crashed and an unknown edit falsely reported success. Add boundary tests at the CLI/model interface. Explain why an old trace summary showing 100% was misleading: it omitted missed lines. The corrected report is reproducible and counts all executable model lines. Do not claim high coverage guarantees correctness. Mention standard-library-only implementation and two locally tested interpreter versions.

## System-in-use demonstration (separate MP4, maximum 4 minutes)

Use an isolated temporary directory. Demonstrate help; create each record type; search using compound conditions and multiword text; edit the result; print details; show an invalid command returning a friendly error; save; delete; load with confirmation; print restored records; exit. Target duration 2-3 minutes. No voice is required by the course for this implementation demo; add short captions for less obvious steps.

tools/demo_session.py produces a timestamped transcript from actual application execution. It may be used to record/render a repeatable console demo. Do not present invented output as a runtime recording. The separate group presentation recording must be performed by real members and is not replaced by this console demonstration.
