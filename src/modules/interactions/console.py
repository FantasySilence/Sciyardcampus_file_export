# ================================================================== #
# @Author: Fantasy_Silence                                           #
# @Time: 2026-11-01                                                  #
# @IDE: Visual Studio Code & PyCharm                                 #
# @Python: 3.9.7                                                     #
# ================================================================== #
# @Description: 交互菜单的终端输入原语（读数字、读是否、选一项）         # 
# ================================================================== #
import unicodedata
from typing import List, Optional


class Console:

    """
    终端输入的几个小工具

    负责"怎么问"
    统一约定：直接回车用默认值，输入 q 一律取消。
    """

    @staticmethod
    def normalize(raw: str) -> str:

        """
        把全角数字、全角字母统一成半角，免得开着中文输入法按不动
        """

        return unicodedata.normalize("NFKC", raw).strip()

    @staticmethod
    def ask_int(prompt: str, default: int, low: int = 1, high: int = 10000) -> Optional[int]:

        """
        问一个整数：直接回车用默认值，输入 q 取消（返回 None）
        """

        while True:

            raw = Console.normalize(input("%s（回车=%d，q 取消）：" % (prompt, default)))

            if raw.lower() == "q":
                return None
            if raw == "":
                return default
            if raw.isdigit() and low <= int(raw) <= high:
                return int(raw)

            print("  请输入 %d ~ %d 之间的数字" % (low, high))

    @staticmethod
    def ask_yes(prompt: str, default: bool = False) -> bool:

        """
        问一个 yes/no：直接回车用默认值
        """

        hint = "Y/n" if default else "y/N"
        raw = Console.normalize(input("%s（%s）：" % (prompt, hint))).lower()

        if raw == "":
            return default
        return raw in ("y", "yes", "是", "1")

    @staticmethod
    def confirm_start(text: str) -> bool:

        """
        采集前的确认：直接回车开始，输入 q 取消（返回 False）
        """

        raw = Console.normalize(input("%s（回车开始，q 取消）：" % text))
        return raw.lower() != "q"

    @staticmethod
    def choose(prompt: str, options: List[str]) -> Optional[int]:

        """
        打印一组编号选项，返回选中的下标（从 0 开始）；0 或 q 返回 None
        """

        print(prompt)
        for index, label in enumerate(options, start=1):
            print("  %d) %s" % (index, label))
        print("  0) 返回")

        while True:

            raw = Console.normalize(input("请选择："))

            if raw.lower() in ("0", "q"):
                return None
            if raw.isdigit() and 1 <= int(raw) <= len(options):
                return int(raw) - 1

            print("  请输入 0 ~ %d 之间的数字" % len(options))

    @staticmethod
    def ask_key(keys: List[str]) -> Optional[str]:

        """
        读主菜单的一个按键：返回 keys 里的某一项；输入 0 或 q 返回 None
        """

        while True:

            raw = Console.normalize(input("\n请选择："))

            if raw.lower() in ("0", "q"):
                return None
            if raw in keys:
                return raw

            print("  请输入 0 ~ %s 之间的数字" % keys[-1])

    @staticmethod
    def pause():

        """
        一个动作结束后停一下，免得日志被菜单刷掉
        """

        try:
            input("\n按回车返回主菜单")
        except (KeyboardInterrupt, EOFError):
            print()
