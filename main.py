"""
数苑校园试卷提取：截图 -> 提取文字 -> 生成 Word

在项目根目录执行：

    python main.py                     # 全套：逐题型截图 -> OCR -> Word -> 核对
    python main.py capture             # 只截图（会提示你把试卷滑到每个题型的开头）
    python main.py capture -t 选择题    # 只截某一种题型
    python main.py probe               # 调试：存一张整屏，打印识别到的题卡位置
    python main.py ocr                 # 只做文字提取
    python main.py word                # 只生成 Word
    python main.py check               # 只打印产物统计

- 截图部分需要模拟器停在对应题型的开头（脚本只往下截，不会回头补），
  所以 capture 会在每个题型开始前停下等你回车；
- OCR 和 Word 只读写 resources/ 里的文件，不需要模拟器。
"""
import os
import argparse

from src.common import const
from src.common.filesio import FilesIO
from src.common.figuresio import FiguresIO
from src.modules.datapreparation.screenshot import GetScreenshot
from src.modules.datapreparation.text_extraction import TextExtraction
from src.modules.process.word_builder import WordBuilder


# ------ 按试卷里的题型和顺序改这里 ------ #
PNG_TYPES = ("选择题", "分析题", "画图题", "计算题")


def capture(png_type=None, pages=10):

    """
    截图：每个题型跑之前，手动把模拟器滑到该题型的开头
    png_type 不传就按 PNG_TYPES 依次处理
    """

    kinds = [png_type] if png_type is not None else list(PNG_TYPES)

    for kind in kinds:
        input("把模拟器里的试卷滑到「%s」开头，回车开始截图：" % kind)
        # ------ 从当前画面往下截，存到 resources/row_pngs/<题型>/ ------ #
        GetScreenshot.save(is_save=True, png_type=kind, pages=pages)
        print()


def extract_text(png_type=None):

    """
    提取文字：row_pngs/<题型>/N.png -> row_txt/<题型>/N.txt
    含公式/表格/图像的分别存成 N_formula.txt、N_table.txt、N_image.txt
    """

    TextExtraction.save(png_type=png_type)


def build_word(png_type=None):

    """
    生成 Word：row_txt 每个题型合成 resources/word_output/<题型>题库.docx
    含公式的题贴原图，没公式的题转成正文
    """

    WordBuilder.save(png_type=png_type)


def check():

    """
    核对产物：每个题型的 图片 / txt / Word 数量
    """

    png_root = FiguresIO.loadFigure()
    txt_root = FilesIO.loadText()
    word_root = FilesIO.loadWord()

    kinds = sorted(os.listdir(txt_root))
    if not kinds:
        print("[提示] row_txt 下还没有东西，先跑 main.py capture 和 main.py ocr")

    for kind in kinds:

        png_dir = os.path.join(png_root, kind)
        pngs = len([name for name in os.listdir(png_dir) if name.endswith(".png")]) if os.path.isdir(png_dir) else 0

        names = os.listdir(os.path.join(txt_root, kind))
        counts = {key: 0 for key in const.OCR_KIND_ORDER}
        for name in names:
            for feature in TextExtraction.kinds_of(name):
                counts[feature] += 1

        docx = os.path.join(word_root, "%s%s.docx" % (kind, const.WORD_TITLE_SUFFIX))

        print("%s：图片 %d 张，txt %d 份（公式 %d、表格 %d、图像 %d），Word %s"
              % (kind, pngs, len(names), counts["formula"], counts["table"], counts["image"],
                 "已生成" if os.path.exists(docx) else "未生成"))

    print()
    print("输出目录：")
    print("  图片：%s" % png_root)
    print("  文本：%s" % txt_root)
    print("  Word：%s" % word_root)


def main():

    parser = argparse.ArgumentParser(description="数苑校园试卷提取：截图 -> 提取文字 -> 生成 Word")
    parser.add_argument(
        "step",
        nargs="?",
        default="all",
        choices=["all", "capture", "probe", "ocr", "word", "check"],
        help="要做哪一步，默认 all（截图 + OCR + Word + 核对）",
    )
    parser.add_argument("-t", "--type", dest="png_type", default=None, help="只处理某一题型，比如 选择题")
    parser.add_argument("-p", "--pages", type=int, default=10, help="每个题型最多截多少道题，默认 10")
    args = parser.parse_args()

    if args.step == "probe":
        # ------ 调试：存一张整屏，看切题位置对不对 ------ #
        GetScreenshot.probe()
    elif args.step == "capture":
        capture(args.png_type, args.pages)
    elif args.step == "ocr":
        extract_text(args.png_type)
    elif args.step == "word":
        build_word(args.png_type)
    elif args.step == "check":
        check()
    else:
        capture(args.png_type, args.pages)
        extract_text(args.png_type)
        build_word(args.png_type)
        check()


if __name__ == "__main__":

    try:
        main()
    except KeyboardInterrupt:
        print("\n已取消")
