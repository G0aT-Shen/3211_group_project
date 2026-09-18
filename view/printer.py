"""Console output formatting kept separate from application logic."""

from model import PIR
from model.exceptions import PIMException


class Printer:
    def print_pir(self, pir: PIR) -> None:
        print(str(pir))

    def print_all(self, pirs: list[PIR]) -> None:
        if not pirs:
            print("没有匹配的 PIR。")
            return
        for pir in pirs:
            self.print_pir(pir)

    def print_msg(self, message: str) -> None:
        print(message)

    def print_error(self, error: PIMException) -> None:
        print(f"错误：{error}")
