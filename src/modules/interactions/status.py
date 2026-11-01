# ================================================================== #
# @Author: Fantasy_Silence                                           #
# @Time: 2026-11-01                                                  #
# @IDE: Visual Studio Code & PyCharm                                 #
# @Python: 3.9.7                                                     #
# ================================================================== #
# @Description: 只读的产物统计与展示：菜单顶部状态 + 核对报表          #
# ================================================================== #
import os
from typing import Dict

from src.common import const
from src.common.filesio import FilesIO
from src.common.figuresio import FiguresIO
from src.modules.tools.android_device import AndroidDevice
from src.modules.datapreparation.text_extraction import TextExtraction


class Status:

    """
    产物统计与展示

    只读：只 listdir、不截图、不写文件。分两处用：
        1. 主菜单顶部那一屏状态（banner）
        2. 菜单 6「检查产物」的报表（report）
    """

    @staticmethod
    def count_pngs(folder: str) -> int:

        """
        数一个目录下有多少张 png
        """

        if not os.path.isdir(folder):
            return 0
        return len([name for name in os.listdir(folder) if name.endswith(".png")])

    @staticmethod
    def count_kinds(folder: str) -> Dict[str, int]:

        """
        数一个 txt 目录里有几道题带公式 / 表格 / 图像
        """

        counts = {key: 0 for key in const.OCR_KIND_ORDER}
        if not os.path.isdir(folder):
            return counts

        for name in os.listdir(folder):
            for feature in TextExtraction.kinds_of(name):
                counts[feature] += 1
        return counts

    @staticmethod
    def kinds_summary() -> str:

        """
        主菜单顶部：分题型各有多少张图
        """

        root = FiguresIO.loadFigure()
        kinds = sorted(name for name in os.listdir(root)
                       if os.path.isdir(os.path.join(root, name)))
        if not kinds:
            return "（还没有图片）"

        return " · ".join("%s %d" % (kind, Status.count_pngs(os.path.join(root, kind)))
                          for kind in kinds)

    @staticmethod
    def papers_summary() -> str:

        """
        主菜单顶部：每一卷的 图 / txt / Word 情况
        """

        root = FiguresIO.loadPaper()
        word_root = FilesIO.loadWord()

        papers = sorted(name for name in os.listdir(root)
                        if os.path.isdir(os.path.join(root, name)))
        if not papers:
            return "（还没有卷子）"

        parts = []
        for paper in papers:
            pngs = Status.count_pngs(os.path.join(root, paper, const.PAPER_PNGS))
            txt_dir = os.path.join(root, paper, const.PAPER_TXTS)
            txts = len(os.listdir(txt_dir)) if os.path.isdir(txt_dir) else 0
            docx = os.path.exists(os.path.join(word_root, "%s.docx" % paper))
            parts.append("%s（图 %d / txt %d / Word %s）"
                         % (paper, pngs, txts, "已生成" if docx else "未生成"))

        return "、".join(parts)

    @staticmethod
    def banner():

        """
        主菜单顶部那一屏：截图通道 + 已有产物
        """

        channel = "adb" if AndroidDevice.adb() is not None else "鼠标（没找到 adb，要求窗口不被遮挡）"

        print()
        print("=" * 62)
        print(" 数苑校园试卷提取")
        print(" 截图通道：%s" % channel)
        print("-" * 62)
        print(" 分题型：%s" % Status.kinds_summary())
        print(" 整卷：  %s" % Status.papers_summary())
        print("=" * 62)

    @staticmethod
    def check_papers(word_root: str) -> str:

        """
        混合试卷的产物统计：每一卷的 图片 / txt / Word 数量
        返回 row_paper 根目录，方便最后打印
        """

        paper_root = FiguresIO.loadPaper()
        papers = sorted(name for name in os.listdir(paper_root)
                        if os.path.isdir(os.path.join(paper_root, name)))

        print()
        if not papers:
            print("[提示] row_paper 下还没有卷子，先在主菜单选 1 或 2 采集一次")
            return paper_root

        print("混合试卷：")
        for paper in papers:

            pngs = Status.count_pngs(os.path.join(paper_root, paper, const.PAPER_PNGS))

            txt_dir = os.path.join(paper_root, paper, const.PAPER_TXTS)
            names = os.listdir(txt_dir) if os.path.isdir(txt_dir) else []
            counts = Status.count_kinds(txt_dir)

            docx = os.path.join(word_root, "%s.docx" % paper)

            print("  %s：图片 %d 张，txt %d 份（公式 %d、表格 %d、图像 %d），Word %s"
                  % (paper, pngs, len(names), counts["formula"], counts["table"], counts["image"],
                     "已生成" if os.path.exists(docx) else "未生成"))

        return paper_root

    @staticmethod
    def report():

        """
        核对产物：分题型与混合试卷各自的图片 / txt / Word 数量
        """

        png_root = FiguresIO.loadFigure()
        txt_root = FilesIO.loadText()
        word_root = FilesIO.loadWord()

        kinds = sorted(name for name in os.listdir(txt_root)
                       if os.path.isdir(os.path.join(txt_root, name)))
        if not kinds:
            print("[提示] row_txt 下还没有东西，先在主菜单选 1~3 采集、选 4 提取文字")

        for kind in kinds:

            pngs = Status.count_pngs(os.path.join(png_root, kind))

            names = os.listdir(os.path.join(txt_root, kind))
            counts = Status.count_kinds(os.path.join(txt_root, kind))

            docx = os.path.join(word_root, "%s%s.docx" % (kind, const.WORD_TITLE_SUFFIX))

            print("%s：图片 %d 张，txt %d 份（公式 %d、表格 %d、图像 %d），Word %s"
                  % (kind, pngs, len(names), counts["formula"], counts["table"], counts["image"],
                     "已生成" if os.path.exists(docx) else "未生成"))

        paper_root = Status.check_papers(word_root)

        print()
        print("输出目录：")
        print("  图片：%s" % png_root)
        print("  文本：%s" % txt_root)
        print("  Word：%s" % word_root)
        print("  混合试卷：%s" % paper_root)
