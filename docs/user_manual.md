# User Manual
COMP3211 PIM | Version 0.2 | macOS / Windows | 5 October 2026

## 1. Start and exit
Open Terminal in the project directory and run python3 main.py. The application prints pim> when it is ready. Enter help for command examples. No third-party installation is required. Data is in memory until you save it. exit or quit ends the program; unsaved changes require y/yes confirmation. A blank answer or n cancels. Ctrl-C cancels an input line or running command and returns to the prompt. After interrupting a command that can change data, inspect the records and save again before exiting: a save may already have committed before the interrupt arrived, and the application conservatively retains the unsaved flag. EOF ends input and warns if unsaved data remains.

On Windows, extract the ZIP to a writable directory and run `.\run_windows.cmd` in PowerShell (or `run_windows.cmd` in CMD). Double-clicking the script also starts the application. It selects Python 3.9+ from PATH or the Python launcher, enables UTF-8, and sets the project as the working directory. Run `.\run_windows.cmd --check` for tests, coverage and syntax checks; failures return a nonzero status. Alternatively use `py -3 -X utf8 main.py` from the project directory. Enter application commands at `pim>`, not at the PowerShell/CMD prompt. If redirected output or a terminal cannot encode a stored character when using a different encoding, the application displays an ASCII escape and continues. Saved files retain the original Unicode text.

## 2. Create records
Commands use English keywords and accept Unicode data. Put multiword text in double or single quotes. Keywords and option names are case-insensitive; stored text keeps its original case.
```text
add text "Buy milk"
add task "Submit report" --deadline 2026-11-19 20:00
add event "Team meeting" --start 2026-10-12 09:00 --alarm 2026-10-12 08:30
add contact --name "Alice" --address "Hong Kong" --mobile "+852 01234567"
```
The response `Created PIR #1` means record 1 was created. Every required field must be nonblank. Mobile numbers are strings: leading zeroes and international prefixes are preserved. The event alarm is saved, displayed and searchable; the application does not issue OS notifications.

Time format is YYYY-MM-DD HH:MM, using local time without an offset. A date alone means 00:00. ISO YYYY-MM-DDTHH:MM and YYYY-MM-DDTHH:MM:00 are also accepted. Invalid dates, offsets and nonzero seconds are rejected. An alarm can precede or follow the start time.

Only space, tab, carriage return and line feed separate words, exactly as in shlex. Other whitespace, including the non-breaking and ideographic spaces produced by some keyboards and pasted text, is ordinary data: it is stored, displayed, searched and saved like any other character. A value that ends with such a character keeps it, so `add text abc　` stores three letters followed by an ideographic space.

## 3. Edit and delete
```text
edit 2 --description "Final report" --deadline 2026-11-20 12:00
edit 3 --start 2026-10-13 09:00 --alarm 2026-10-13 08:30
edit 4 --mobile "+852 61234567"
edit 1 --text "Buy coffee"
delete 1
```
Several fields can be changed together. If any field is invalid, none is changed. start and start_time name the same event field. IDs and types cannot be edited. Each option may appear only once. Unknown or inappropriate fields produce an error. Deletion takes effect in memory immediately; save writes it to disk. Deleted IDs are never reused within that collection.

## 4. Search
```text
search text contains "buy milk"
search type = task && deadline < 2026-12-01
search (type = task || type = event) && !description contains "cancelled"
search name contains "Alice" || mobile contains "0123"
search alarm = "2026-10-12 08:30"
search 'text contains "hello world"'
```
A search expression may be entered directly or inside a single outer pair of quotes. The outer pair only groups the expression: the command parser removes it and passes the text inside it unchanged to the search tokenizer, so both entry forms tokenize the same expression and select the same records. The outer pair must enclose the entire expression; a character left outside it stays part of the expression. The same word rule as in section 2 applies: a literal that ends with whitespace other than space, tab, carriage return or line feed keeps that character and matches only records that contain it. For nested quotations, use different quote styles as in the last example; a backslash-escaped inner quote is literal text rather than a nesting mechanism, exactly as it is in the direct form. Backslashes follow POSIX shlex rules; a literal Windows-style path should use single quotes. Escaped spaces and adjacent quote fragments also work: `search text = buy\ milk` and `search text = 'buy '"milk"` both look for `buy milk`. Escaped operators are literal text. Quote text beginning with -- to preserve it as data: `add text "--todo"`, `edit 1 --text "--archived"` and `search text contains "--"` are valid. Unquoted option tokens still require a following value. Malformed quoted searches report an error and leave the current collection and session usable.

Fields: type for all records; text for notes; description for tasks/events; deadline for tasks; start/start_time and alarm for events; name/address/mobile for contacts. Type supports = and !=. Text supports contains, = and !=, all case-insensitive using Unicode casefold. Dates support < <= > >= = !=. Empty contains "" matches every record that has that text field.

Precedence is !, then &&, then ||. Use parentheses when intent is unclear. A condition on a field absent from a record is False, even for !=. Negation reverses that Boolean result. Therefore deadline != 2027-01-01 matches tasks only, but !deadline = 2027-01-01 also matches notes/events/contacts. Results are ordered by ID.

## 5. Inspect records
```text
print all
print
print 2
```
A record appears as `#ID [type]` followed by all its fields. Task/event timestamps show minute precision. Contacts show address and mobile without numeric conversion. `No matching PIRs.` means the result or collection is empty. A missing positive ID produces `Error: PIR #ID was not found` rather than a blank record.

## 6. Save and load
```text
save
save "my records.pim"
load "my records.pim"
```
save defaults to pim.pim in the directory where you started the program. The suffix must be .pim, case-insensitively. Use an absolute path to choose another directory; the parent directory must already exist. Saving over an existing file asks for y/yes confirmation. A negative/blank answer leaves the file unchanged.

The Windows launcher starts in the project folder, so its default save location is that folder. Use single quotes around Windows backslash paths: `save 'C:\Users\Professor\Desktop\review folder\records.pim'` and `load 'C:\Users\Professor\Desktop\review folder\records.pim'`. Forward slashes are also accepted. An unquoted backslash is an escape in the command grammar and can change the path. Ordinary UNC paths work when single-quoted. On Windows, reserved device names (including extensions, such as CON.pim), alternate data streams, invalid characters, components ending in a space/dot, and device/extended namespace paths are rejected before filesystem access. Use ordinary local/UNC paths. UTF-8 .pim files can be moved between macOS and Windows, including files with LF or CRLF line endings.

load replaces the entire current collection, not merges it. The file is validated first. Unsaved changes require confirmation before replacement. A successful save/load clears the unsaved flag. A failed load keeps the current records. A failed write/replacement preserves the old file.

Files are UTF-8 JSON containing schema_version=1, next_id and pirs. Unsupported schemas, repeated IDs/keys, unknown fields, bad dates or missing metadata are rejected. Files are limited to 10 MiB. Loading accepts only regular files; symbolic links, named pipes and devices are rejected. Use one writing process per file and keep a separate backup of valuable information.

## 7. Errors and limits
Errors start with `Error:` and explain the invalid command or data. For example `print abc` reports an invalid ID, `delete` without an argument shows usage, and `edit 1 --unknown x` rejects the field. The next command remains usable. Wrong dates and incomplete quotes do not create or partially edit records. Arguments are read exactly as typed, so trailing whitespace outside the POSIX set belongs to the argument: `print 1　` with an ideographic space is not the ID 1, while `print 1 ` with an ordinary space is.

Limits: 16,384 characters per command; 8,192 per search expression; 64 nested Boolean/parenthesis levels; positive ASCII IDs up to 100 digits; 10 MiB per saved file. Fields cannot be blank. These checks bound accidental or malformed input, not a security sandbox. Terminal control sequences in personally supplied data are outside the intended trusted local input model.

The same numeric ID limit applies to loaded records and model operations. After allocating the largest ID (100 nines), the collection reports that its ID space is exhausted. Existing records remain printable, editable, deletable and saveable. The persisted next_id may be 10^100 solely as an exhausted marker; deleting records does not reset that marker or reuse their IDs. Larger next_id values are rejected.

## 8. Troubleshooting
File not found: confirm the path and working directory. Permission denied: choose a directory you own and check file permissions. Bad schema: restore a backup or fix a copy, never discard the only original. An unsupported Python version: run python3 --version and use Python 3.9 or later. If interrupted by EOF with unsaved edits, those edits were not written automatically.
