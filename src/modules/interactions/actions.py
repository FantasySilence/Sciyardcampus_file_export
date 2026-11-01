# ================================================================== #
# @Author: Fantasy_Silence                                           #
# @Time: 2026-11-01                                                  #
# @IDE: Visual Studio Code & PyCharm                                 #
# @Python: 3.9.7                                                     #
# ================================================================== #
# @Description: 菜单选中之后用于采集 / 提取文字 / 导出 Word             #
# ================================================================== #
import os

from src.common import const
from src.common.figuresio import FiguresIO
from src.modules.interactions.console import Console
from src.modules.process.word_builder import WordBuilder
from src.modules.datapreparation.screenshot import GetScreenshot
from src.modules.process.paper_word_builder import PaperWordBuilder
from src.modules.datapreparation.text_extraction import TextExtraction
from src.modules.datapreparation.paper_screenshot import GetPaperScreenshot
from src.modules.datapreparation.paper_text_extraction import PaperTextExtraction


class Actions:

    """
    动作层：会动模拟器或写文件的那些事
    只读统计和展示在 Status 里，问答流程在 Menus 里，不打印菜单。
    """

    @staticmethod
    def capture(png_type=None, pages: int = const.DEFAULT_PAGES):

        """
        截图：每个题型跑之前，手动把模拟器滑到该题型的开头
        png_type 不传就按 const.PNG_TYPES 依次处理
        """

        kinds = [png_type] if png_type is not None else list(const.PNG_TYPES)

        for kind in kinds:
            if not Console.confirm_start("把模拟器里的试卷滑到「%s」开头" % kind):
                print("[提示] 已取消")
                return
            # ------ 从当前画面往下截，存到 resources/row_pngs/<题型>/ ------ #
            GetScreenshot.save(is_save=True, png_type=kind, pages=pages)
            print()

    @staticmethod
    def capture_paper(paper: str, pages: int = const.DEFAULT_PAGES):

        """
        整卷采集：存到 resources/row_paper/<卷名>/pngs/，文件名是顺序号
        开跑前会问要不要清空旧图
        """

        folder = FiguresIO.loadPaper(paper=paper)
        olds = [name for name in os.listdir(folder) if name.endswith(".png")]
        if olds:
            print("[提示] %s\\%s 下已有 %d 张旧图，同名的会被覆盖"
                  % (paper, const.PAPER_PNGS, len(olds)))
            if Console.ask_yes("开跑前先清空这些旧图？", False):
                for name in olds:
                    os.remove(os.path.join(folder, name))
                print("[提示] 已清空 %d 张旧图" % len(olds))

        GetPaperScreenshot.save(paper=paper, pages=pages, is_save=True)

    @staticmethod
    def extract_text(png_type=None, paper=None):

        """
        提取文字
        - 分题型：row_pngs/<题型>/N.png -> row_txt/<题型>/N.txt
        - 混合试卷（传了 paper）：row_paper/<卷名>/pngs/N.png -> row_paper/<卷名>/txts/N.txt
        含公式/表格/图像的分别存成 N_formula.txt、N_table.txt、N_image.txt
        """

        if paper:
            PaperTextExtraction.save(paper=paper)
        else:
            TextExtraction.save(png_type=png_type)

    @staticmethod
    def build_word(png_type=None, paper=None):

        """
        生成 Word
        - 分题型：row_txt 每个题型合成 resources/word_output/<题型>题库.docx
        - 混合试卷（传了 paper）：row_paper/<卷名>/txts 合成 resources/word_output/<卷名>.docx
        含公式/表格/图像的题贴原图，纯文字题转成正文
        """

        if paper:
            PaperWordBuilder.save(paper=paper)
        else:
            WordBuilder.save(png_type=png_type)
