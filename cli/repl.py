"""CLI adapter: translate validated commands into model operations."""
from __future__ import annotations
from controller import PIMManager, PIRFactory
from model.exceptions import InvalidCommandError, PIMException, StorageError
from storage import Storage
from storage.storage import pim_path
from view import Printer
from .command_parser import Command, CommandParser
from .search_parser import SearchParser

HELP = """Commands:
  add text "text"
  add task "description" --deadline YYYY-MM-DD HH:MM
  add event "description" --start YYYY-MM-DD HH:MM --alarm YYYY-MM-DD HH:MM
  add contact --name "name" --address "address" --mobile "+852 61234567"
  edit <id> --text "text" (or other fields for that type; multiple fields allowed)
  search text contains "buy milk"
  search type = task && deadline < YYYY-MM-DD
  print [id|all]     delete <id>
  save [file.pim]    load <file.pim>
  help              exit / quit
Times are local and have minute precision; a date alone means 00:00.
Search supports contains, = != < <= > >=, ! && || and parentheses.
Text comparisons are case-insensitive; precedence is ! > && > ||.
save defaults to pim.pim. Confirm with y before overwriting or discarding unsaved changes.
alarm is a stored record field; this application does not send OS notifications."""


class Repl:
    def __init__(self, manager: PIMManager | None = None, storage: Storage | None = None, printer: Printer | None = None, confirm=None) -> None:
        self.manager = manager if manager is not None else PIMManager()
        self.storage = storage or Storage()
        self.printer = printer or Printer()
        self.parser = CommandParser()
        self.search_parser = SearchParser()
        self.dirty = False
        self._confirm_handler = confirm

    def _confirm(self, prompt: str) -> bool:
        if self._confirm_handler is not None:
            return bool(self._confirm_handler(prompt))
        try:
            return input(prompt + " [y/N] ").strip().lower() in {"y", "yes"}
        except (EOFError, KeyboardInterrupt):
            return False

    def run(self) -> None:
        self.printer.print_msg("PIM started. Enter help for commands, or exit to quit.")
        while True:
            try:
                line = input("pim> ")
            except EOFError:
                if self.dirty:
                    self.printer.print_msg("Input ended with unsaved changes.")
                break
            except KeyboardInterrupt:
                self.printer.print_msg("Input cancelled; use exit to quit.")
                continue
            if not line.strip():
                continue
            command = None
            try:
                command = self.parser.parse(line)
                if self.execute(command):
                    break
            except KeyboardInterrupt:
                # An interrupt may arrive after a mutation/commit but before its
                # dirty flag update. Keep the exit confirmation in that case.
                if command is not None and command.name in {"add", "edit", "delete", "save", "load"}:
                    self.dirty = True
                self.printer.print_msg("Command cancelled; use exit to quit. Check records before saving.")
            except PIMException as exc:
                self.printer.print_error(exc)

    def execute(self, command: Command) -> bool:
        name = command.name
        if name == "exit":
            if self.dirty and not self._confirm("Discard unsaved changes and exit?"):
                self.printer.print_msg("Exit cancelled.")
                return False
            self.printer.print_msg("Goodbye.")
            return True
        if name == "help":
            self.printer.print_msg(HELP)
        elif name == "add":
            pir = self.manager.add_pir(PIRFactory.create(command.args[0], command.options))
            self.dirty = True
            self.printer.print_msg(f"Created PIR #{pir.get_id()}")
        elif name == "edit":
            pir = self.manager.edit_pir(int(command.args[0]), command.options)
            self.dirty = True
            self.printer.print_msg(f"Updated PIR #{pir.get_id()}")
        elif name == "search":
            self.printer.print_all(self.manager.search(self.search_parser.parse(command.args[0])))
        elif name == "print":
            target = command.args[0] if command.args else "all"
            self.printer.print_all(self.manager.list_all() if target.lower() == "all" else [self.manager.get_pir(int(target))])
        elif name == "delete":
            self.manager.delete_pir(int(command.args[0]))
            self.dirty = True
            self.printer.print_msg(f"Deleted PIR #{command.args[0]}")
        elif name == "save":
            path = command.args[0] if command.args else "pim.pim"
            try:
                exists = pim_path(path).exists()
            except OSError as exc:
                raise StorageError(f"Could not inspect file path {path}: {exc}") from exc
            if exists and not self._confirm(f"Overwrite existing file {path}?"):
                self.printer.print_msg("Save cancelled.")
                return False
            self.storage.save(path, self.manager)
            self.dirty = False
            self.printer.print_msg(f"Saved to {path}")
        elif name == "load":
            # Read and validate before offering to replace the active model.
            loaded = self.storage.load(command.args[0])
            if self.dirty and not self._confirm("Loading will replace unsaved changes. Continue?"):
                self.printer.print_msg("Load cancelled.")
                return False
            self.manager = loaded
            self.dirty = False
            self.printer.print_msg(f"Loaded {len(self.manager.pirs)} records")
        else:
            raise InvalidCommandError(f"Unknown command: {name}")
        return False
