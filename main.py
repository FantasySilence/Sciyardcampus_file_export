# ============================================= #
# @Author: Fantasy_Silence                      #
# @Time: 2026-10-31                             #
# @IDE: Visual Studio Code & PyCharm            #
# @Python: 3.9.7                                #
# ============================================= #
# @Description: 数苑校园试卷提取工具主程序入口    #
# ============================================= #

"""
数苑校园试卷提取：截图 -> 提取文字 -> 生成 Word

在项目根目录执行：

    python main.py                     # 全套：逐题型截图 -> OCR -> Word -> 核对
    python main.py capture             # 只截图（会提示你把试卷滑到每个题型的开头）
    python main.py capture -t 选择题    # 只截某一种题型
    python main.py paper -n 期中卷      # 混合试卷：整卷一次滚到底，按顺序号存图
    python main.py probe               # 调试：存一张整屏，打印识别到的题卡位置
    python main.py ocr                 # 只做文字提取
    python main.py ocr -n 期中卷        # 只提取混合试卷的文字（row_paper/<卷名>/txts）
    python main.py word                # 只生成 Word
    python main.py word -n 期中卷       # 混合试卷导 Word（word_output/期中卷.docx）
    python main.py check               # 只打印产物统计

- 截图部分需要模拟器停在对应题型的开头（脚本只往下截，不会回头补），
  所以 capture 会在每个题型开始前停下等你回车；
- paper 是给"一份卷子里好几类题型混在一起"的情况用的：整卷从最上面滚到底，
  图存在 resources/row_paper/<卷名>/ 下，文件名是顺序号 1.png、2.png …；
- OCR 和 Word 只读写 resources/ 里的文件，不需要模拟器（目前只处理分题型目录）。
"""
import os
import argparse

from src.common import const
from src.common.filesio import FilesIO
from src.common.figuresio import FiguresIO
from src.modules.datapreparation.screenshot import GetScreenshot
from src.modules.datapreparation.paper_screenshot import GetPaperScreenshot
from src.modules.datapreparation.text_extraction import TextExtraction
from src.modules.datapreparation.paper_text_extraction import PaperTextExtraction
from src.modules.process.word_builder import WordBuilder
from src.modules.process.paper_word_builder import PaperWordBuilder


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


def capture_paper(paper=None, pages=2000, fresh=False):

    """
    混合试卷截图：整卷一次滚到底，存到 resources/row_paper/<卷名>/，文件名是顺序号
    paper 是卷名，不传就用 -n/--name 指定
    """

    if not paper:
        print("[错误] 用 -n/--name 指定卷名，比如 python main.py paper -n 期中卷")
        return

    if fresh:
        folder = FiguresIO.loadPaper(paper=paper)
        olds = [name for name in os.listdir(folder) if name.endswith(".png")]
        for name in olds:
            os.remove(os.path.join(folder, name))
        print("[提示] 已清空 %s\\%s 下 %d 张旧图" % (paper, const.PAPER_PNGS, len(olds)))

    input("把模拟器里的试卷滑到最上面，回车开始截图：")
    GetPaperScreenshot.save(paper=paper, pages=pages, is_save=True)
    print()


def extract_text(png_type=None, paper=None):

    """
    提取文字
    - 分题型：row_pngs/<题型>/N.png -> row_txt/<题型>/N.txt
    - 混合试卷（给了 -n/--name）：row_paper/<卷名>/pngs/N.png -> row_paper/<卷名>/txts/N.txt
    含公式/表格/图像的分别存成 N_formula.txt、N_table.txt、N_image.txt
    """

    if paper:
        PaperTextExtraction.save(paper=paper)
    else:
        TextExtraction.save(png_type=png_type)


def build_word(png_type=None, paper=None):

    """
    生成 Word
    - 分题型：row_txt 每个题型合成 resources/word_output/<题型>题库.docx
    - 混合试卷（给了 -n/--name）：row_paper/<卷名>/txts 合成 resources/word_output/<卷名>.docx
    含公式/表格/图像的题贴原图，纯文字题转成正文
    """

    if paper:
        PaperWordBuilder.save(paper=paper)
    else:
        WordBuilder.save(png_type=png_type)


def count_pngs(folder):

    """
    数一个目录下有多少张 png
    """

    if not os.path.isdir(folder):
        return 0
    return len([name for name in os.listdir(folder) if name.endswith(".png")])


def count_kinds(folder):

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


def check_papers(word_root):

    """
    混合试卷的产物统计：每一卷的 图片 / txt / Word 数量
    返回 row_paper 根目录，方便最后打印
    """

    paper_root = FiguresIO.loadPaper()
    papers = sorted(name for name in os.listdir(paper_root)
                    if os.path.isdir(os.path.join(paper_root, name)))

    print()
    if not papers:
        print("[提示] row_paper 下还没有卷子，先跑 main.py paper -n <卷名>")
        return paper_root

    print("混合试卷：")
    for paper in papers:

        pngs = count_pngs(os.path.join(paper_root, paper, const.PAPER_PNGS))

        txt_dir = os.path.join(paper_root, paper, const.PAPER_TXTS)
        names = os.listdir(txt_dir) if os.path.isdir(txt_dir) else []
        counts = count_kinds(txt_dir)

        docx = os.path.join(word_root, "%s.docx" % paper)

        print("  %s：图片 %d 张，txt %d 份（公式 %d、表格 %d、图像 %d），Word %s"
              % (paper, pngs, len(names), counts["formula"], counts["table"], counts["image"],
                 "已生成" if os.path.exists(docx) else "未生成"))

    return paper_root


def check():

    """
    核对产物：分题型与混合试卷各自的 图片 / txt / Word 数量
    """

    png_root = FiguresIO.loadFigure()
    txt_root = FilesIO.loadText()
    word_root = FilesIO.loadWord()

    kinds = sorted(name for name in os.listdir(txt_root)
                   if os.path.isdir(os.path.join(txt_root, name)))
    if not kinds:
        print("[提示] row_txt 下还没有东西，先跑 main.py capture 和 main.py ocr")

    for kind in kinds:

        pngs = count_pngs(os.path.join(png_root, kind))

        names = os.listdir(os.path.join(txt_root, kind))
        counts = count_kinds(os.path.join(txt_root, kind))

        docx = os.path.join(word_root, "%s%s.docx" % (kind, const.WORD_TITLE_SUFFIX))

        print("%s：图片 %d 张，txt %d 份（公式 %d、表格 %d、图像 %d），Word %s"
              % (kind, pngs, len(names), counts["formula"], counts["table"], counts["image"],
                 "已生成" if os.path.exists(docx) else "未生成"))

    paper_root = check_papers(word_root)

    print()
    print("输出目录：")
    print("  图片：%s" % png_root)
    print("  文本：%s" % txt_root)
    print("  Word：%s" % word_root)
    print("  混合试卷：%s" % paper_root)


def main():

    parser = argparse.ArgumentParser(description="数苑校园试卷提取：截图 -> 提取文字 -> 生成 Word")
    parser.add_argument(
        "step",
        nargs="?",
        default="all",
        choices=["all", "capture", "paper", "probe", "ocr", "word", "check"],
        help="要做哪一步，默认 all（截图 + OCR + Word + 核对）",
    )
    parser.add_argument("-t", "--type", dest="png_type", default=None, help="只处理某一题型，比如 选择题")
    parser.add_argument("-p", "--pages", type=int, default=None,
                        help="最多截多少道题：capture 默认 10，paper 默认 2000")
    parser.add_argument("-n", "--name", dest="paper", default=None, help="混合试卷的卷名（paper 步骤用），比如 期中卷")
    parser.add_argument("--fresh", action="store_true", help="混合试卷开跑前先清空该卷文件夹里的旧图")
    args = parser.parse_args()

    if args.step == "probe":
        # ------ 调试：存一张整屏，看切题位置对不对 ------ #
        GetScreenshot.probe()
    elif args.step == "capture":
        capture(args.png_type, args.pages if args.pages is not None else 10)
    elif args.step == "paper":
        capture_paper(args.paper, args.pages if args.pages is not None else 2000, args.fresh)
    elif args.step == "ocr":
        extract_text(args.png_type, args.paper)
    elif args.step == "word":
        build_word(args.png_type, args.paper)
    elif args.step == "check":
        check()
    else:
        capture(args.png_type, args.pages if args.pages is not None else 10)
        extract_text(args.png_type)
        build_word(args.png_type)
        check()


if __name__ == "__main__":

    try:
        main()
    except KeyboardInterrupt:
        print("\n已取消")
