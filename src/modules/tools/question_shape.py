# ================================================================== #
# @Author: Fantasy_Silence                                           #
# @Time: 2026-10-29                                                  #
# @IDE: Visual Studio Code & PyCharm                                 #
# @Python: 3.9.7                                                     #
# ================================================================== #
# @Description: 从题卡图片判断有没有表格、有没有图像（图形）           #
# ================================================================== #
import numpy as np
from PIL import Image
from typing import List

from src.common import const


class QuestionShape:

    """
    看一张题卡的"版面长相"，判断它是不是表格题、图形题

    只处理版面：公式是按 OCR 出来的文字判断的，那部分在 TextExtraction 里。

    判据（阈值都在 const 里，按 1600 宽的题卡标定）：

        表格 —— 有几条贯穿全宽的长横线，还有几条贯穿大半高的长竖线；
                课件的表格边框是浅灰细线，靠"长直线"很好认。
        图像 —— 连续一大片行里都有墨迹。文字是一行一行的，行与行之间必然有空行，
                所以只要连续 100 行没有空白行，基本就是插了图（曲线、示意图）。
    """

    @staticmethod
    def dark_mask(image: Image.Image) -> np.ndarray:

        """
        把题卡转成"哪里有内容"的布尔矩阵
        """

        array = np.asarray(image.convert("L")).astype(int)
        return array < const.SHAPE_DARK_LUM

    @staticmethod
    def max_runs(mask: np.ndarray) -> np.ndarray:

        """
        每一行里最长的连续 True 长度；对转置矩阵调用就是每一列的结果

        做法：先算出每个位置"左边最近的空白下标"（没有就记 -1），
        长度 = 当前位置 - 那个下标
        """

        height, width = mask.shape
        if width == 0:
            return np.zeros(height, dtype=int)

        column = np.arange(width)
        last_gap = np.maximum.accumulate(np.where(mask, -1, column), axis=1)
        lengths = np.where(mask, column - last_gap, 0)
        return lengths.max(axis=1)

    @staticmethod
    def longest_span(flags: np.ndarray) -> int:

        """
        一维布尔序列里最长的连续 True 长度
        """

        if flags.size == 0:
            return 0

        index = np.arange(flags.size)
        last_gap = np.maximum.accumulate(np.where(flags, -1, index))
        lengths = np.where(flags, index - last_gap, 0)
        return int(lengths.max())

    @staticmethod
    def widen(mask: np.ndarray, radius: int, axis: int) -> np.ndarray:

        """
        沿某个方向把墨迹"抹宽"几个像素

        表格是一格一格画的，格与格之间会留 1~3 像素的缝，不补齐的话
        整条边框会被切成几段，长直线就找不出来了
        """

        result = mask.copy()
        for shift in range(1, radius + 1):
            if axis == 1:
                result[:, shift:] |= mask[:, :-shift]
                result[:, :-shift] |= mask[:, shift:]
            else:
                result[shift:, :] |= mask[:-shift, :]
                result[:-shift, :] |= mask[shift:, :]
        return result

    @staticmethod
    def line_positions(runs: np.ndarray, need: int) -> List[int]:

        """
        找出"够长的线"的位置（行号或列号）

        线本身有粗细，相邻几行/几列其实是同一条，所以连续的行号并成一条，
        位置取这几行的中间值
        """

        hits = np.nonzero(runs >= need)[0]
        if hits.size == 0:
            return []

        groups = np.split(hits, np.nonzero(np.diff(hits) > 2)[0] + 1)
        return [int(group.mean()) for group in groups]

    @staticmethod
    def has_table(mask: np.ndarray) -> bool:

        """
        有几条长横线 + 几条长竖线，就是表格

        横线按画面宽度、竖线按画面高度算"够不够长"，所以居中的小表格也能认出来
        """

        height, width = mask.shape

        h_need = max(int(const.SHAPE_TABLE_H_RATIO * width), const.SHAPE_TABLE_H_MIN)
        v_need = max(int(const.SHAPE_TABLE_V_RATIO * height), const.SHAPE_TABLE_V_MIN)

        horizontal = QuestionShape.line_positions(
            QuestionShape.max_runs(QuestionShape.widen(mask, const.SHAPE_LINE_GAP, 1)), h_need
        )
        vertical = QuestionShape.line_positions(
            QuestionShape.max_runs(QuestionShape.widen(mask, const.SHAPE_LINE_GAP, 0)), v_need
        )

        return len(horizontal) >= const.SHAPE_TABLE_H_LINES and len(vertical) >= const.SHAPE_TABLE_V_LINES

    @staticmethod
    def has_figure(mask: np.ndarray) -> bool:

        """
        连续 SHAPE_FIGURE_SPAN 行都有墨迹，就认为有图像
        """

        row_ink = mask.sum(axis=1)
        return QuestionShape.longest_span(row_ink >= 3) >= const.SHAPE_FIGURE_SPAN

    @staticmethod
    def kinds(image: Image.Image) -> List[str]:

        """
        返回这张题卡的版面特征：["table"] / ["image"] / []

        有表格就不再判图像：表格本身也是"连续有墨迹"，会被误判成图像
        """

        mask = QuestionShape.dark_mask(image)
        if QuestionShape.has_table(mask):
            return ["table"]
        if QuestionShape.has_figure(mask):
            return ["image"]
        return []
