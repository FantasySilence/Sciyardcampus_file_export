# ================================================================== #
# @Author: Fantasy_Silence                                           #
# @Time: 2026-11-01                                                  #
# @IDE: Visual Studio Code & PyCharm                                 #
# @Python: 3.9.7                                                     #
# ================================================================== #
# @Description: 菜单项的问答流程与分发（问参数 -> 调 Actions / Status）  #
# ================================================================== #
import os
from typing import Optional

from src.common import const
from src.common.figuresio import FiguresIO
from src.modules.interactions.status import Status
from src.modules.interactions.console import Console
from src.modules.interactions.actions import Actions
from src.modules.datapreparation.screenshot import GetScreenshot


class Menus:

    """
    菜单项清单 + 每一项的问答流程

    每个方法做三件事：问参数、调 Actions / Status、暂停等回车。
    主菜单的循环本身在 main.py 的 start() 里。
    """

    # ------ 菜单项：加一项只改这里（key、说明），再在 run() 里加一个分支 ------ #
    ITEMS = (
        ("1", "整卷：采集 + 文字 + Word + 核对"),
        ("2", "整卷：只采集"),
        ("3", "单题型：采集"),
        ("4", "文字提取（OCR）"),
        ("5", "导出 Word"),
        ("6", "检查产物"),
        ("7", "调试：看当前画面的切题结果"),
    )

    KEYS = tuple(key for key, _ in ITEMS)

    # ------ 本次运行里用过的卷名，问卷名时当默认值 ------ #
    LAST_PAPER = "期中卷"

    @staticmethod
    def show():

        """
        打印菜单项
        """

        for key, label in Menus.ITEMS:
            print("  %s) %s" % (key, label))
        print("  0) 退出")

    @staticmethod
    def run(key: str):

        """
        按主菜单的按键分发
        """

        if key == "1":
            Menus.paper(True)
        elif key == "2":
            Menus.paper(False)
        elif key == "3":
            Menus.single_type()
        elif key == "4":
            Menus.text()
        elif key == "5":
            Menus.word()
        elif key == "6":
            Menus.check()
        elif key == "7":
            Menus.probe()

    @staticmethod
    def ask_paper() -> Optional[str]:

        """
        问卷名：列出已有卷子做参考，直接回车用上次的；q 取消返回 None
        """

        root = FiguresIO.loadPaper()
        papers = sorted(name for name in os.listdir(root)
                        if os.path.isdir(os.path.join(root, name)))

        if papers:
            print("  已有卷子：%s" % "、".join(papers))
            if Menus.LAST_PAPER not in papers:
                Menus.LAST_PAPER = papers[-1]

        while True:

            raw = Console.normalize(input("卷名（回车=%s，q 取消）：" % Menus.LAST_PAPER))

            if raw.lower() == "q":
                return None

            name = raw or Menus.LAST_PAPER
            if not name:
                print("  卷名不能为空")
                continue
            if any(char in name for char in '\\/:*?"<>|'):
                print('  卷名里不能带 \\ / : * ? " < > |')
                continue

            Menus.LAST_PAPER = name
            return name

    @staticmethod
    def paper(all_in_one: bool):

        """
        整卷：采集（all_in_one=True 时接着做文字、Word、核对）
        """

        paper = Menus.ask_paper()
        if paper is None:
            return

        pages = Console.ask_int("最多采集多少题", const.DEFAULT_PAGES)
        if pages is None:
            return

        if not Console.confirm_start("把模拟器里的试卷滑到最上面"):
            print("[提示] 已取消")
            Console.pause()
            return

        Actions.capture_paper(paper, pages)
        print()

        if all_in_one:
            Actions.extract_text(paper=paper)
            print()
            Actions.build_word(paper=paper)
            print()
            Status.report()

        Console.pause()

    @staticmethod
    def single_type():

        """
        单题型：采集（可以连 OCR + Word 一起做）
        """

        index = Console.choose("选择题型：", list(const.PNG_TYPES) + ["全部依次"])
        if index is None:
            return

        kinds = [const.PNG_TYPES[index]] if index < len(const.PNG_TYPES) else list(const.PNG_TYPES)

        pages = Console.ask_int("最多抓多少题", const.DEFAULT_PAGES)
        if pages is None:
            return

        # ------ 采集本身（选「全部依次」就逐个题型停下来确认） ------ #
        Actions.capture(None if index >= len(const.PNG_TYPES) else const.PNG_TYPES[index], pages)

        if Console.ask_yes("继续提取文字并导出 Word？", False):
            for kind in kinds:
                Actions.extract_text(png_type=kind)
                Actions.build_word(png_type=kind)
                print()

        Console.pause()

    @staticmethod
    def text():

        """
        文字提取：全部题型 / 指定题型 / 某一卷
        """

        index = Console.choose("选择范围：", ["全部题型", "指定题型", "某一卷"])
        if index is None:
            return

        if index == 0:
            Actions.extract_text()
        elif index == 1:
            kind = Console.choose("选择题型：", list(const.PNG_TYPES))
            if kind is None:
                return
            Actions.extract_text(png_type=const.PNG_TYPES[kind])
        else:
            paper = Menus.ask_paper()
            if paper is None:
                return
            Actions.extract_text(paper=paper)

        Console.pause()

    @staticmethod
    def word():

        """
        导出 Word：全部题型 / 指定题型 / 某一卷
        """

        index = Console.choose("选择范围：", ["全部题型", "指定题型", "某一卷"])
        if index is None:
            return

        if index == 0:
            Actions.build_word()
        elif index == 1:
            kind = Console.choose("选择题型：", list(const.PNG_TYPES))
            if kind is None:
                return
            Actions.build_word(png_type=const.PNG_TYPES[kind])
        else:
            paper = Menus.ask_paper()
            if paper is None:
                return
            Actions.build_word(paper=paper)

        Console.pause()

    @staticmethod
    def check():

        """
        检查产物
        """

        Status.report()
        Console.pause()

    @staticmethod
    def probe():

        """
        调试：截一张整屏，存成 row_pngs/_probe.png，并打印题卡位置、题目编号
        不滑动、不改动已有数据，用来排查切题位置对不对
        """

        GetScreenshot.probe()
        Console.pause()
