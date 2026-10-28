# ================================================================== #
# @Author: Fantasy_Silence                                           #
# @Time: 2026-10-29                                                  #
# @IDE: Visual Studio Code & PyCharm                                 #
# @Python: 3.9.7                                                     #
# ================================================================== #
# @Description: 从整屏画面里识别并裁出"一道题"                         #
# ================================================================== #
import numpy as np
from PIL import Image
from typing import List, NamedTuple, Tuple

from src.common import const


class Card(NamedTuple):

    """
    一张题卡在整屏画面里占的行区间（单位是虚拟机像素）
    """

    header_top: int          # "题目N（x分）"标题行的上沿
    top: int                 # 题干第一行文字的上沿
    bottom: int              # 最后一行选项文字的下沿
    footer: int              # 页脚"单选题 | 易 ..."那行灰字的上沿，-1 表示没看到

    def complete(self) -> bool:

        """题干没被顶部标题栏挡住，而且这道题的页脚也在画面里"""

        return self.top > const.CARD_SAFE_TOP and self.footer > 0

    def cut_bottom(self) -> bool:

        """题干看得见、页脚还没露出来，说明被画面下边缘切掉了（下一屏就是它）"""

        return self.top > const.CARD_SAFE_TOP and self.footer < 0


class QuestionCard:

    """
    从整屏画面里切出"一道题"

    切出来的效果：只有题干和 A/B/C/D 选项，
    既不带"题目3（1分）"那行标题，也不带"单选题 | 易 ... 共享试题"那行页脚。

    识别依据（数苑这套试卷页面的固定样式）：

        1. 每道题的标题行里有红色"（x分）"，用纯红像素定位每道题的起点；
        2. 正文是深色字（亮度 140 以下），页脚"单选题 | 易 ... 共享试题"是浅灰字
           （亮度 165 以上），靠亮度差把页脚从正文里摘出去；
        3. 正文下面能读到页脚，说明这道题在画面里完整露出来了，可以截；
        4. 两道题之间隔着下一题的标题行，所以"本题的下边界"就是下一题的标题行。
    """

    @staticmethod
    def runs(mask: np.ndarray) -> List[Tuple[int, int]]:

        """
        把 True 的连续行合并成区间，隔 1 行以上才算断开
        """

        rows: List[Tuple[int, int]] = []
        for index in (int(value) for value in np.nonzero(mask)[0]):
            if rows and index - rows[-1][1] <= 1:
                rows[-1] = (rows[-1][0], index)
            else:
                rows.append((index, index))
        return rows

    @staticmethod
    def split(frame: Image.Image) -> List[Card]:

        """
        找出画面里每一道题的区间，按从上到下的顺序返回
        """

        array = np.asarray(frame.convert("RGB")).astype(int)
        height, width = array.shape[:2]
        lum = array.mean(axis=2)

        # ------ 大统一：这里算出来的行号一律换算成"虚拟机像素"，和截图缩放无关 ------ #
        scale = width / const.EMULATOR_WIDTH

        # ------ 红字 / 有内容 / 深色正文 三种按行的掩码 ------ #
        red = array[:, :, 0] > const.CARD_RED[0]
        red &= array[:, :, 1] < const.CARD_RED[1]
        red &= array[:, :, 2] < const.CARD_RED[2]
        ink = lum < 200
        dark_rows = (lum < const.CARD_DARK_LUM).any(axis=1)

        # ------ 页脚是浅灰字：这一行最暗的像素也够亮，才算页脚 ------ #
        footer_area = ink[:, :const.CARD_FOOTER_WIDTH]
        footer_min = np.where(footer_area, lum[:, :const.CARD_FOOTER_WIDTH], 255.0).min(axis=1)
        footer_rows = footer_area.any(axis=1) & (footer_min > const.CARD_FOOTER_LUM)

        # ------ 文字行的顶边会有一两行浅灰的抗锯齿像素，太矮的段不算页脚 ------ #
        footers = [
            (top, bottom) for top, bottom in QuestionCard.runs(footer_rows)
            if bottom - top >= const.CARD_FOOTER_MIN
        ]

        # ------ 红字只占"（x分）"几个字，补成它所在的那一整行标题 ------ #
        ink_runs = QuestionCard.runs(ink.any(axis=1))
        headers = []
        for red_top, _ in QuestionCard.runs(red.any(axis=1)):
            for ink_top, ink_bottom in ink_runs:
                if ink_top <= red_top <= ink_bottom:
                    headers.append((ink_top, ink_bottom))
                    break

        # ------ 两条标题行之间就是一道题，深色正文的首尾就是题干和最后一行选项 ------ #
        cards = []
        for index, (header_top, header_bottom) in enumerate(headers):
            limit = headers[index + 1][0] if index + 1 < len(headers) else height
            body = np.nonzero(dark_rows[header_bottom + 1:limit])[0]
            if len(body) == 0:
                continue
            bottom = header_bottom + 1 + int(body[-1])

            # ------ 正文下面那行浅灰页脚露出来，就说明这道题在画面里完整了 ------ #
            footer = -1
            for footer_top, _ in footers:
                if footer_top > bottom:
                    footer = footer_top
                    break

            cards.append(
                Card(
                    header_top=int(round(header_top / scale)),
                    top=int(round((header_bottom + 1 + int(body[0])) / scale)),
                    bottom=int(round(bottom / scale)),
                    footer=-1 if footer < 0 else int(round(footer / scale)),
                )
            )
        return cards

    @staticmethod
    def crop(frame: Image.Image, card: Card) -> Image.Image:

        """
        按裁一张题卡：左右整幅，上下各留一点白
        """

        width, height = frame.size
        scale = width / const.EMULATOR_WIDTH
        top = max(0, int(round((card.top - const.CARD_TOP_MARGIN) * scale)))
        bottom = min(height, int(round((card.bottom + const.CARD_BOTTOM_MARGIN) * scale)))
        return frame.crop((0, top, width, bottom))

    @staticmethod
    def fingerprint(image: Image.Image) -> np.ndarray:

        """
        题卡的黑白缩略图（True 表示有字），用来判断两张图是不是同一道题
        同一道题即使因为滚动相位差整体错开一两像素，差异比例也很小；
        不同题目的文字不一样，差异比例会明显变大
        """

        gray = np.asarray(image.convert("L").resize(const.THUMB_SIZE), dtype=int)
        return gray < const.THUMB_INK_LUM
