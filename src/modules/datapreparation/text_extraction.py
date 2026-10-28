# ================================================================== #
# @Author: Fantasy_Silence                                           #
# @Time: 2026-10-29                                                  #
# @IDE: Visual Studio Code & PyCharm                                 #
# @Python: 3.9.7                                                     #
# ================================================================== #
# @Description: 把题目截图识别成文字，一道题一个 txt                    #
# ================================================================== #
import os
import re
import glob
from PIL import Image
from typing import List, Optional, Tuple

from src.common import const
from src.common.filesio import FilesIO
from src.common.figuresio import FiguresIO
from src.modules.tools.ocr import Ocr


class TextExtraction:

    """
    把 row_pngs/<题型>/N.png 识别成文字，存到 row_txt/<题型>/ 下：
    没有公式的存 N.txt，有公式的存 N_formula.txt（一眼能挑出来核对）。

    识别用Tesseract（chi_sim+eng）：中文正文靠得住，
    但截图里的公式是斜体，变量和上下标容易被认错（Q_d 常被认成 O,，
    P 常被认成尸/7），所以公式片段统一用 $...$ 包起来——这样 txt 里的公式
    位置是明确的，后面交给 pandoc 转 Word 时会变成公式对象，也方便逐条核对。

    txt 的格式：题干、每个选项、每个小问各是一个自然段，段与段之间空一行，
    这样 pandoc（markdown 读入）能正确分段，python-docx 那边跳过空行即可。
    只想拿到一堆纯文字、不做公式标记的话，把 mark_math 的调用去掉即可。
    """

    # ------ 选项行：A/B/C/D 开头 ------ #
    OPTION = re.compile(r"^[ABCD][\s\u4e00-\u9fff]")

    # ------ 小问：(1) （1） 开头 ------ #
    SUB_ITEM = re.compile(r"^[（(]\d+[）)]")

    # ------ 公式片段：字母、数字、运算符、括号，中间允许空格 ------ #
    # 前后都不许从单词中间起止，中间遇到三个以上连续字母（HARMS、Dale 这种整词）就断开，
    # 这样一段里的公式和识别出来的乱码词能分开处理
    MATH = re.compile(
        r"(?<![A-Za-z])(?:(?![A-Za-z]{3})[A-Za-z0-9()\[\]{}^_.,+\-*/=<>\u00b7\u00d7\u00f7\u2264\u2265\u2260 ]){3,}(?![A-Za-z])"
    )

    # ------ 公式里的排版符号 -> LaTeX ------ #
    SYMBOLS = {
        "\u00d7": r"\times ",
        "\u00f7": r"\div ",
        "\u2264": r"\leq ",
        "\u2265": r"\geq ",
        "\u2260": r"\neq ",
        "\u00b7": r"\cdot ",
    }

    @staticmethod
    def prepare():

        """
        找到 tesseract.exe（交给 Ocr 统一处理）
        """

        Ocr.prepare()

    @staticmethod
    def types() -> List[str]:

        """
        row_pngs 下的题型文件夹（单选题、计算题 ...）
        """

        root = FiguresIO.loadFigure()
        return sorted(name for name in os.listdir(root) if os.path.isdir(os.path.join(root, name)))

    @staticmethod
    def order(path: str) -> int:

        """
        按文件名里的题号排序，不是数字的文件返回 -1
        """

        try:
            return int(os.path.splitext(os.path.basename(path))[0])
        except ValueError:
            return -1

    @staticmethod
    def paragraphs(text: str) -> List[str]:

        """
        把 OCR 出来的行整理成"题干 / 每个选项 / 每个小问"各一段
        换行截断的续行会被接回上一段；整行都是公式的行单独成段，
        免得把公式和乱码粘成一大段
        """

        paragraphs: List[str] = []
        for line in (row.strip() for row in text.splitlines()):
            if not line:
                continue
            if not paragraphs or TextExtraction.OPTION.match(line) \
                    or TextExtraction.SUB_ITEM.match(line) or TextExtraction.is_math_line(line):
                paragraphs.append(line)
            else:
                paragraphs[-1] = TextExtraction.merge(paragraphs[-1], line)
        return paragraphs

    @staticmethod
    def is_math_line(line: str) -> bool:

        """
        这一行是不是几乎只有英文数字（公式行），这种行不往上一段里并
        """

        chars = [char for char in line if not char.isspace()]
        if not chars:
            return False
        if sum(1 for char in chars if char.isalnum()) < 3:
            return False
        return sum(1 for char in chars if char.isascii()) / len(chars) >= 0.6

    @staticmethod
    def merge(previous: str, line: str) -> str:

        """
        拼接续行：中文直接接上，两侧都是英文/数字时补一个空格
        """

        if previous and line and previous[-1].isascii() and previous[-1].isalnum() \
                and line[0].isascii() and line[0].isalnum():
            return previous + " " + line
        return previous + line

    @staticmethod
    def is_formula(run: str) -> bool:

        """
        判断一段英文数字是不是公式：有等号/上下标，或者字母数字连写（20P、6P）
        """

        run = run.strip()
        if len(run) < 3 or not any(char.isalnum() for char in run):
            return False
        if any(operator in run for operator in ("=", "^", "_")):
            return True
        return re.search(r"[A-Za-z]\d|\d[A-Za-z]", run) is not None

    @staticmethod
    def mark_math(paragraph: str) -> Tuple[str, bool]:

        """
        把段落里的公式片段包成 $...$，返回 (处理后的段落, 是否含公式)
        从右往左替换，避免改动前面片段的下标
        """

        found = False
        for match in reversed(list(TextExtraction.MATH.finditer(paragraph))):

            formula = match.group(0).strip()

            # ------ 结尾的标点留在公式外面 ------ #
            tail = ""
            while formula and formula[-1] in ",.;:，。；：":
                tail = formula[-1] + tail
                formula = formula[:-1]

            # ------ 夹着整词（Dale、HRSA）的多半是识别出来的乱码，不当公式 ------ #
            if not TextExtraction.is_formula(formula) or re.search(r"[A-Za-z]{3,}", formula):
                continue

            # ------ 去掉多余空白，符号换成 LaTeX ------ #
            formula = re.sub(r"\s+", " ", formula)
            for symbol, latex in TextExtraction.SYMBOLS.items():
                formula = formula.replace(symbol, latex)
            formula = re.sub(r"\s*([=+*/^_])\s*", r"\1", formula)
            formula = re.sub(r"\s*-\s*", "-", formula)

            paragraph = paragraph[:match.start()] + "$" + formula + "$" + tail + paragraph[match.end():]
            found = True
        return paragraph, found

    @staticmethod
    def write(path: str, png_type: str, index: int) -> Tuple[bool, str]:

        """
        识别一张题图并写成 txt，返回 (这段文字里有没有公式, 文件名)
        含公式的存成 1_formula.txt，不含的存成 1.txt
        """

        image = Image.open(path).convert("RGB")
        if const.OCR_SCALE != 1:
            image = image.resize(
                (image.size[0] * const.OCR_SCALE, image.size[1] * const.OCR_SCALE),
                Image.LANCZOS,
            )

        text = Ocr.text(image, lang=const.TESSERACT_LANG, config=const.TESSERACT_CONFIG)

        has_math = False
        paragraphs: List[str] = []
        for paragraph in TextExtraction.paragraphs(text):
            line, found = TextExtraction.mark_math(paragraph)
            has_math = has_math or found
            paragraphs.append(line)

        # ------ 含公式的在文件名上标注，方便挑出来人工核对 ------ #
        name = "%d%s.txt" % (index, const.OCR_FORMULA_SUFFIX) if has_math else "%d.txt" % index
        target = FilesIO.loadText(name, png_type)
        with open(target, "w", encoding="utf-8") as file:
            file.write("\n\n".join(paragraphs) + "\n")

        # ------ 同一道题上一次生成的另一种命名清掉，免得 1.txt 和 1_formula.txt 并存 ------ #
        other = FilesIO.loadText(
            "%d.txt" % index if has_math else "%d%s.txt" % (index, const.OCR_FORMULA_SUFFIX),
            png_type,
        )
        if os.path.exists(other):
            os.remove(other)

        print("已保存 %s\\%s（%d 段%s）"
              % (png_type, name, len(paragraphs), "，含公式" if has_math else ""))
        return has_math, name

    @staticmethod
    def save(png_type: Optional[str] = None, indexes: Optional[List[int]] = None):

        """
        png_type: 题型（子文件夹名），不传就处理 row_pngs 下的所有题型
        indexes: 只识别指定题号，比如 [1, 2]；不传就全部识别
        """

        TextExtraction.prepare()

        kinds = [png_type] if png_type is not None else TextExtraction.types()
        if not kinds:
            print("[提示] row_pngs 下还没有题型文件夹，先跑 test_3.py 截图")
            return

        review: List[str] = []
        for kind in kinds:

            paths = sorted(glob.glob(os.path.join(FiguresIO.loadFigure(sub_dir=kind), "*.png")),
                           key=TextExtraction.order)
            if not paths:
                continue

            for path in paths:
                index = TextExtraction.order(path)
                if index <= 0:
                    continue
                if indexes is not None and index not in indexes:
                    continue
                has_math, name = TextExtraction.write(path, kind, index)
                if has_math:
                    review.append("%s/%s" % (kind, name))

        if review:
            print("[提示] 下面这些 txt 里有公式，OCR 对斜体变量容易认错，建议逐条核对：")
            for item in review:
                print("    " + item)
