"""Interactive command loop."""

from __future__ import annotations

from controller import PIMManager, PIRFactory
from model.exceptions import InvalidCommandError, PIMException
from storage import Storage
from view import Printer

from .command_parser import Command, CommandParser
from .search_parser import SearchParser


class Repl:
    def __init__(self, manager: PIMManager | None = None, storage: Storage | None = None, printer: Printer | None = None) -> None:
        self.manager = manager or PIMManager()
        self.storage = storage or Storage()
        self.printer = printer or Printer()
        self.parser = CommandParser()
        self.search_parser = SearchParser()

    def run(self) -> None:
        self.printer.print_msg("PIM 已启动。输入 help 查看命令，输入 exit 退出。")
        while True:
            try:
                line = input("pim> ")
            except EOFError:
                self.printer.print_msg("")
                break
            if not line.strip():
                continue
            try:
                if self.execute(self.parser.parse(line)):
                    break
            except PIMException as exc:
                self.printer.print_error(exc)

    def execute(self, command: Command) -> bool:
        name = command.name
        if name == "exit":
            self.printer.print_msg("再见。")
            return True
        if name == "help":
            self.printer.print_msg("add text|task|event|contact ... | edit <id> --field value | search <expr> | print [id|all] | delete <id> | save [file] | load <file> | exit")
            return False
        if name == "add":
            pir = self.manager.add_pir(PIRFactory.create(command.args[0], command.options))
            self.printer.print_msg(f"已创建 PIR #{pir.get_id()}")
        elif name == "edit":
            pir = self.manager.edit_pir(int(command.args[0]), command.options)
            self.printer.print_msg(f"已更新 PIR #{pir.get_id()}")
        elif name == "search":
            self.printer.print_all(self.manager.search(self.search_parser.parse(command.args[0])))
        elif name == "print":
            target = command.args[0] if command.args else "all"
            self.printer.print_all(self.manager.list_all() if target.lower() == "all" else [self.manager.get_pir(int(target))])
        elif name == "delete":
            self.manager.delete_pir(int(command.args[0]))
            self.printer.print_msg(f"已删除 PIR #{command.args[0]}")
        elif name == "save":
            path = command.args[0] if command.args else "pim.pim"
            self.storage.save(path, self.manager)
            self.printer.print_msg(f"已保存到 {path}")
        elif name == "load":
            if not command.args:
                raise InvalidCommandError("用法：load <file>")
            self.manager = self.storage.load(command.args[0])
            self.printer.print_msg(f"已加载 {len(self.manager.pirs)} 条记录")
        return False
