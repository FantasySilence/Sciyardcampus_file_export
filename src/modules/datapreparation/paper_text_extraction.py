# ================================================================== #
# @Author: Fantasy_Silence                                           #
# @Time: 2026-11-01                                                  #
# @IDE: Visual Studio Code & PyCharm                                 #
# @Python: 3.9.7                                                     #
# ================================================================== #
# @Description: 混合试卷的文字提取：一张图一个 txt，存到卷子的 txts 目录  #
# ================================================================== #
import os
import glob
from PIL import Image
from typing import List, Optional, Tuple

from src.common import const
from src.common.filesio import FilesIO
from src.common.figuresio import FiguresIO
from src.modules.tools.ocr import Ocr
from src.modules.tools.question_shape import QuestionShape
from src.modules.datapreparation.text_extraction import TextExtraction


class PaperTextExtraction:

    """
    混合试卷的文字提取

    思路和分题型完全一样，只是目录换了、文件名是顺序号：

        row_paper/<卷名>/pngs/1.png  ->  row_paper/<卷名>/txts/1.txt
                                         1_formula.txt / 1_table.txt / 1_image.txt
                                         多个特征按 formula -> table -> image 拼

    分段、公式标记、版面判断（表格/图像）都直接复用 TextExtraction 和
    QuestionShape 里那套已经调过的逻辑，这里只负责"从哪读、往哪写"。
    """

    @staticmethod
    def prepare():

        """
        找到 tesseract.exe（交给 Ocr 统一处理）
        """

        TextExtraction.prepare()

    @staticmethod
    def write(path: str, paper: str, index: int) -> Tuple[List[str], str]:

        """
        识别一张题图并写成 txt，返回 (特征标签, 文件名)
        index 是顺序号，和 pngs 里的图片编号一一对应
        """

        image = Image.open(path).convert("RGB")

        # ------ 表格/图像看版面，用原始尺寸判断（阈值按 1600 宽标定） ------ #
        shapes = QuestionShape.kinds(image)

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

        # ------ 公式看文字，表格/图像看版面，合起来拼后缀 ------ #
        kinds = (["formula"] if has_math else []) + shapes
        suffix = "".join(const.OCR_KIND_SUFFIX[kind] for kind in const.OCR_KIND_ORDER if kind in kinds)

        name = "%d%s.txt" % (index, suffix)
        target = FilesIO.loadPaperText(name, paper)
        with open(target, "w", encoding="utf-8") as file:
            file.write("\n\n".join(paragraphs) + "\n")

        # ------ 这道题以前生成的其它命名清掉，免得新旧文件名并存 ------ #
        folder = FilesIO.loadPaperText(paper=paper)
        olds = glob.glob(os.path.join(folder, "%d_*.txt" % index))
        olds.append(os.path.join(folder, "%d.txt" % index))
        for old in olds:
            if os.path.exists(old) and os.path.basename(old) != name:
                os.remove(old)

        labels = {"formula": "含公式", "table": "含表格", "image": "含图像"}
        note = "，".join(labels[kind] for kind in const.OCR_KIND_ORDER if kind in kinds)
        print("已保存 %s\\%s\\%s（%d 段%s）"
              % (paper, const.PAPER_TXTS, name, len(paragraphs), "，" + note if note else ""))
        return kinds, name

    @staticmethod
    def save(paper: str, indexes: Optional[List[int]] = None):

        """
        paper: 卷名，读 row_paper/<卷名>/pngs/，写 row_paper/<卷名>/txts/
        indexes: 只识别指定顺序号，比如 [1, 2]；不传就全部识别
        """

        if not paper:
            print("[错误] 卷名不能为空，比如 PaperTextExtraction.save(paper=\"期中卷\")")
            return

        PaperTextExtraction.prepare()

        folder = FiguresIO.loadPaper(paper=paper)
        paths = [path for path in sorted(glob.glob(os.path.join(folder, "*.png")),
                                         key=TextExtraction.order)
                 if TextExtraction.order(path) > 0]

        if not paths:
            print("[提示] %s\\%s 下还没有图片，先跑一次截图" % (paper, const.PAPER_PNGS))
            return

        print("[提示] 开始识别 %s：共 %d 张图" % (paper, len(paths)))

        review: List[str] = []
        for path in paths:

            index = TextExtraction.order(path)
            if indexes is not None and index not in indexes:
                continue

            kinds, name = PaperTextExtraction.write(path, paper, index)
            if kinds:
                review.append("%s/%s" % (paper, name))

        if review:
            print("[提示] 下面这些 txt 标了公式/表格/图像，OCR 不一定认得准，建议对着原图逐条核对：")
            for item in review:
                print("    " + item)
