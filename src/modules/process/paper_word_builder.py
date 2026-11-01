# ================================================================== #
# @Author: Fantasy_Silence                                           #
# @Time: 2026-11-01                                                  #
# @IDE: Visual Studio Code & PyCharm                                 #
# @Python: 3.9.7                                                     #
# ================================================================== #
# @Description: 把混合试卷的题目图片和 txt 合成一份 Word               #
# ================================================================== #
import os
import re
import glob
from docx import Document
from typing import List, Optional, Tuple

from src.common import const
from src.common.filesio import FilesIO
from src.common.figuresio import FiguresIO
from src.modules.process.word_builder import WordBuilder


class PaperWordBuilder:

    """
    混合试卷的 Word 导出：resources/word_output/<卷名>.docx

    规则和分题型一样，按 txt 的文件名决定用哪种：
        1_formula.txt / 1_table.txt / 1_image.txt（含组合）
                      —— 有公式、表格或图像，OCR 认不准、转文字会丢内容，直接贴原图；
        1.txt         —— 纯文字的题，把段落原样写成正文。

    页面设置、标题、贴图、读段落全部复用 WordBuilder，这里只负责
    "从卷子的 pngs/txts 读、往 word_output/<卷名>.docx 写"。
    """

    @staticmethod
    def indexes(paper: str) -> List[int]:

        """
        这一卷里有哪些题（按 1.txt / 1_formula.txt 这类文件名取顺序号）
        """

        root = FilesIO.loadPaperText(paper=paper)
        indexes = set()
        for name in os.listdir(root):
            match = re.match(r"^(\d+)", name)
            if match:
                indexes.add(int(match.group(1)))
        return sorted(indexes)

    @staticmethod
    def build(paper: str) -> Optional[Tuple[str, int, int]]:

        """
        生成这一卷的 Word，返回 (文件路径, 文字题数, 图片题数)
        """

        indexes = PaperWordBuilder.indexes(paper)
        if not indexes:
            print("[提示] %s\\%s 下没有 txt，先跑一次文字提取" % (paper, const.PAPER_TXTS))
            return None

        document = Document()
        WordBuilder.setup(document)

        txt_root = FilesIO.loadPaperText(paper=paper)
        png_root = FiguresIO.loadPaper(paper=paper)

        text_count = 0
        image_count = 0
        for index in indexes:

            tagged = sorted(glob.glob(os.path.join(txt_root, "%d_*.txt" % index)))
            plain_txt = os.path.join(txt_root, "%d.txt" % index)
            png_path = os.path.join(png_root, "%d.png" % index)

            # ------ 标了公式/表格/图像：贴原图 ------ #
            if tagged:
                WordBuilder.add_title(document, index)
                if os.path.exists(png_path):
                    WordBuilder.add_picture(document, png_path)
                    image_count += 1
                else:
                    print("[警告] %s\\%s\\%d.png 不存在，%s 退化成文字"
                          % (paper, const.PAPER_PNGS, index, os.path.basename(tagged[0])))
                    WordBuilder.add_text(document, tagged[0])
                    text_count += 1
                continue

            # ------ 纯文字：转文字 ------ #
            if os.path.exists(plain_txt):
                WordBuilder.add_title(document, index)
                WordBuilder.add_text(document, plain_txt)
                text_count += 1
                continue

            print("[提示] %s 第 %d 题没有 txt，跳过" % (paper, index))

        target = FilesIO.loadWord("%s.docx" % paper)
        document.save(target)
        return target, text_count, image_count

    @staticmethod
    def save(paper: str):

        """
        paper: 卷名，读 row_paper/<卷名>/txts（配图从 pngs 拿），写 word_output/<卷名>.docx
        """

        if not paper:
            print("[错误] 卷名不能为空，比如 PaperWordBuilder.save(paper=\"期中卷\")")
            return

        result = PaperWordBuilder.build(paper)
        if result is None:
            return

        target, text_count, image_count = result
        print("已保存 %s（文字 %d 题，图片 %d 题）"
              % (os.path.basename(target), text_count, image_count))
