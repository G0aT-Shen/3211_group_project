"""CLI adapter: translate validated commands into model operations."""
from __future__ import annotations
from controller import PIMManager, PIRFactory
from model.exceptions import InvalidCommandError, PIMException, StorageError
from storage import Storage
from storage.storage import pim_path
from view import Printer
from .command_parser import Command, CommandParser
from .search_parser import SearchParser

HELP = """命令：
  add text "内容"
  add task "描述" --deadline 2026-11-19 20:00
  add event "描述" --start 2026-10-12 09:00 --alarm 2026-10-12 08:30
  add contact --name "姓名" --address "地址" --mobile "+852 61234567"
  edit <id> --text "内容" （或该类型的其它字段，可一次修改多个）
  search text contains "买牛奶"
  search type = task && deadline < 2026-12-01
  print [id|all]     delete <id>
  save [file.pim]    load <file.pim>
  help              exit / quit
时间为本地时间，精度为分钟；日期单独输入代表 00:00。
搜索支持 contains、= != < <= > >=、! && || 和括号。
文本比较不区分大小写；优先级 ! > && > ||。
save 默认 pim.pim。覆盖、丢弃未保存修改时须输入 y 确认。
alarm 是记录字段，本程序不触发系统通知。"""


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
        self.printer.print_msg("PIM 已启动。输入 help 查看命令，输入 exit 退出。")
        while True:
            try:
                line = input("pim> ")
            except EOFError:
                if self.dirty:
                    self.printer.print_msg("输入已结束：存在未保存的修改。")
                break
            except KeyboardInterrupt:
                self.printer.print_msg("输入已取消；使用 exit 退出。")
                continue
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
            if self.dirty and not self._confirm("存在未保存修改，退出并丢弃？"):
                self.printer.print_msg("已取消退出。")
                return False
            self.printer.print_msg("再见。")
            return True
        if name == "help":
            self.printer.print_msg(HELP)
        elif name == "add":
            pir = self.manager.add_pir(PIRFactory.create(command.args[0], command.options))
            self.dirty = True
            self.printer.print_msg(f"已创建 PIR #{pir.get_id()}")
        elif name == "edit":
            pir = self.manager.edit_pir(int(command.args[0]), command.options)
            self.dirty = True
            self.printer.print_msg(f"已更新 PIR #{pir.get_id()}")
        elif name == "search":
            self.printer.print_all(self.manager.search(self.search_parser.parse(command.args[0])))
        elif name == "print":
            target = command.args[0] if command.args else "all"
            self.printer.print_all(self.manager.list_all() if target.lower() == "all" else [self.manager.get_pir(int(target))])
        elif name == "delete":
            self.manager.delete_pir(int(command.args[0]))
            self.dirty = True
            self.printer.print_msg(f"已删除 PIR #{command.args[0]}")
        elif name == "save":
            path = command.args[0] if command.args else "pim.pim"
            try:
                exists = pim_path(path).exists()
            except OSError as exc:
                raise StorageError(f"无法检查文件路径 {path}: {exc}") from exc
            if exists and not self._confirm(f"覆盖已有文件 {path}？"):
                self.printer.print_msg("已取消保存。")
                return False
            self.storage.save(path, self.manager)
            self.dirty = False
            self.printer.print_msg(f"已保存到 {path}")
        elif name == "load":
            # Read and validate before offering to replace the active model.
            loaded = self.storage.load(command.args[0])
            if self.dirty and not self._confirm("加载会替换未保存修改，继续？"):
                self.printer.print_msg("已取消加载。")
                return False
            self.manager = loaded
            self.dirty = False
            self.printer.print_msg(f"已加载 {len(self.manager.pirs)} 条记录")
        else:
            raise InvalidCommandError(f"未知命令：{name}")
        return False
