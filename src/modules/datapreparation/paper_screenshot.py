# ================================================================== #
# @Author: Fantasy_Silence                                           #
# @Time: 2026-11-01                                                  #
# @IDE: Visual Studio Code & PyCharm                                 #
# @Python: 3.9.7                                                     #
# ================================================================== #
# @Description: 混合试卷爬取：整卷一次滚到底，按顺序号存图              #
# ================================================================== #
import os
import time
import hashlib
import numpy as np
from typing import Dict, List, Optional, Set, Tuple

from src.common import const
from src.common.figuresio import FiguresIO
from src.modules.tools.android_device import AndroidDevice
from src.modules.tools.question_card import Card, QuestionCard
from src.modules.datapreparation.screenshot import GetScreenshot


class GetPaperScreenshot:

    """
    混合试卷爬取（一份卷子里选择题、分析题、计算题混在一起）

    和分题型截图（GetScreenshot）只有两处不同：

        1. 整卷里每类题型的题号都从 1 开始，题号不再是唯一键，所以「身份」是
           (分区, 题号)；分区靠页脚那行的题型名确认（"… | 单选题 | 易"）；
        2. 文件名用顺序号（1.png、2.png ...），不跟题号走。

    滚动对齐、到底判定、防"长按选中题干"这些全部复用 GetScreenshot 里
    已经验证过的逻辑，这里只写混合卷自己的那点状态机。
    """

    @staticmethod
    def save(paper: str, pages: int = 2000, is_save: bool = True):

        """
        paper: 卷名，存到 resources/row_paper/<卷名>/
        pages: 最多存多少道题（整卷跑给大一点，截到底会自己停）
        从当前画面位置开始往下截，所以运行前先把试卷滑到最上面
        """

        if not paper:
            print("[错误] 卷名不能为空，比如 GetPaperScreenshot.save(paper=\"期中卷\")")
            return

        if const.VERBOSE:
            GetScreenshot.show_info()

        # ------ 提示一下旧图，同名（顺序号）会被覆盖 ------ #
        folder = FiguresIO.loadPaper(paper=paper)
        olds = [name for name in os.listdir(folder) if name.endswith(".png")]
        if olds:
            print("[提示] %s\\%s 下已有 %d 张旧图，同名的会被覆盖"
                  % (paper, const.PAPER_PNGS, len(olds)))
        print("[提示] 输出目录：%s" % folder)

        # ------ 睡5s，便于打开题目页面 ------ #
        time.sleep(5)

        seq = 0                                 # 已存张数，也就是顺序号
        section = 1                             # 分区号：换一类题型就 +1
        current_type: Optional[str] = None      # 当前题型（页脚读出来的）
        last_number: Optional[int] = None       # 当前分区最后一题的题号
        saved_keys: Set[Tuple[int, Optional[int]]] = set()
        skipped_keys: Set[Tuple[int, Optional[int]]] = set()
        recent: List[np.ndarray] = []
        counts: Dict[str, int] = {}
        skipped: List[str] = []
        boundaries: List[Tuple[Optional[int], Optional[int]]] = []
        last_frame = None
        still = 0

        for _ in range(pages * 6 + 10):

            frame = GetScreenshot.capture_clean()
            if frame is None:
                return

            height = frame.size[1]
            cards = QuestionCard.split(frame)
            if not cards:
                print("[错误] 没识别到题目，检查画面是否停在试卷页面（标题行要有红色“（x分）”）")
                return

            numbers = [QuestionCard.header_number(frame, card) for card in cards]

            # ------ 把这一屏里完整露出来的新题都存下来 ------ #
            for card, number in zip(cards, numbers):

                if not card.complete():
                    continue

                # ------ 题号往回走了：多半是换题型了，读页脚确认一下 ------ #
                # 等于上一题的不用管：那是刚存过、往下滚之后仍然完整的同一道题
                if number is not None and last_number is not None and number < last_number:

                    kind = QuestionCard.footer_type(frame, card)
                    pair = (last_number, number)

                    if kind is not None and kind == current_type:
                        print("[提示] 读到编号 %d，和上一题的 %d 对不上，按未读出处理"
                              % (number, last_number))
                        number = None
                    elif pair not in boundaries:
                        boundaries.append(pair)
                        section += 1
                        last_number = None
                        if kind is not None:
                            print("[提示] 题型切换：%s -> %s（下一张存为 %d.png）"
                                  % (current_type, kind, seq + 1))
                            current_type = kind
                        else:
                            print("[提示] 编号从 %d 回到 %d，当作新的一段（页脚题型没读出来）"
                                  % (pair[0], pair[1]))

                # ------ 题号往前跳太远：当识别错误 ------ #
                elif number is not None and last_number is not None \
                        and number > last_number + const.PAPER_JUMP:
                    print("[提示] 读到编号 %d，和上一题的 %d 差太远，按未读出处理"
                          % (number, last_number))
                    number = None

                # ------ 这一分区、这个题号已经存过 ------ #
                if number is not None and (section, number) in saved_keys:
                    continue

                image = QuestionCard.crop(frame, card)
                signature = QuestionCard.fingerprint(image)

                # ------ 兜底防重：只有题号读不出来时，才退回指纹比较 ------ #
                # 题号读得出来、且这一分区里没存过，就说明它一定是新题，
                # 这时候再拿指纹去比会把"长得像"的两道不同题误杀
                if number is None and GetPaperScreenshot.repeated(signature, recent):
                    continue

                # ------ 落盘 + 记账 ------ #
                seq += 1
                if number is not None:
                    saved_keys.add((section, number))
                    last_number = number

                # ------ 第一次存图时把题型定下来，后面才有标签可打 ------ #
                if current_type is None:
                    current_type = QuestionCard.footer_type(frame, card)

                recent.append(signature)
                if len(recent) > const.PAPER_RECENT:
                    recent.pop(0)

                if is_save:
                    name = "%d.png" % seq
                    image.save(FiguresIO.loadPaper(name, paper))
                    print("已保存 %s\\%s\\%s（%s 题目%s，%d x %d）"
                          % (paper, const.PAPER_PNGS, name, current_type or "未知",
                             number if number is not None else "?",
                             image.size[0], image.size[1]))

                label = current_type or "未知"
                counts[label] = counts.get(label, 0) + 1

                # ------ 整卷题号如果连续（不重置），靠这里换题型标签 ------ #
                if seq % const.PAPER_TYPE_CHECK_EVERY == 0:
                    kind = QuestionCard.footer_type(frame, card)
                    if kind is not None and kind != current_type:
                        print("[提示] 题型切换：%s -> %s" % (current_type, kind))
                        current_type = kind

                if seq >= pages:
                    print("[提示] 已达到 pages=%d，停止" % pages)
                    GetPaperScreenshot.summary(seq, counts, skipped)
                    return

            # ------ 下一道被下边缘切掉的题就是目标，按它决定滑多少 ------ #
            target, target_number = GetPaperScreenshot.first_unsaved(
                cards, numbers, section, last_number, saved_keys, skipped_keys
            )

            if target is None:
                scroll = int(height * 0.5)
            else:
                scroll = GetScreenshot.target_scroll(target, height)

                # ------ 已经在目标位置还是存不下来，说明这题一屏放不下 ------ #
                if abs(scroll) <= 20:
                    key = (section, target_number)
                    if key not in skipped_keys:
                        skipped_keys.add(key)
                        label = str(target_number) if target_number is not None else "未知"
                        skipped.append(label)
                        print("[提示] 编号 %s 这题一屏放不下，已跳过（可手动补截）" % label)
                    scroll = int(height * GetScreenshot.TALL_RATIO)

            # ------ 画面没变：先加大距离重试，连续几帧不动才认为到底 ------ #
            digest = hashlib.md5(frame.tobytes()).hexdigest()
            if digest == last_frame:
                still += 1
                if still >= GetScreenshot.STILL_LIMIT:
                    print("[提示] 连续 %d 帧画面没有变化，判定已经到底" % still)
                    break
                print("[提示] 画面没有变化，加大距离重试")
                AndroidDevice.swipe(int(height * 0.6) if abs(scroll) < 60 else int(scroll * 1.2))
                time.sleep(1)
                continue

            still = 0
            last_frame = digest

            AndroidDevice.swipe(scroll)
            time.sleep(1)

        GetPaperScreenshot.summary(seq, counts, skipped)

    @staticmethod
    def first_unsaved(
        cards: List[Card],
        numbers: List[Optional[int]],
        section: int,
        last_number: Optional[int],
        saved_keys: Set[Tuple[int, Optional[int]]],
        skipped_keys: Set[Tuple[int, Optional[int]]],
    ) -> Tuple[Optional[Card], Optional[int]]:

        """
        画面里第一道「被下边缘切掉、还没存过」的题，没有就返回 (None, None)

        被顶部标题栏压住的卡不算目标：往下滚它自然就完整了，拿它当目标会算出
        几像素的滑动——那种滑动在 Android 眼里就是长按，会选中题干。
        """

        for card, number in zip(cards, numbers):

            if card.complete():
                continue

            if card.header_top <= const.CARD_SAFE_TOP:
                continue

            if number is not None:
                key = (section, number)
                if key in skipped_keys:
                    continue
                # ------ 题号比当前分区最后一题小，多半是新一段的第一题，不能按"存过"跳过 ------ #
                if key in saved_keys and number > (last_number or 0):
                    continue

            return card, number

        return None, None

    @staticmethod
    def repeated(signature: np.ndarray, recent: List[np.ndarray]) -> bool:

        """
        和最近保存的几张比指纹：同一道题跨帧出现时裁剪尺寸一致、差异很小

        这道判断只做兜底（题型读错、题号读错时防止同一题存两遍），
        阈值和分题型那边一样，取严一些免得把两道不同的题判成同一道
        """

        for saved in recent:
            if saved.shape != signature.shape:
                continue
            if float(np.logical_xor(saved, signature).mean()) < const.SAME_RATIO:
                return True
        return False

    @staticmethod
    def summary(total: int, counts: Dict[str, int], skipped: List[str]):

        """
        结束汇报：一共多少道、按题型分开、哪些一屏放不下被跳过了
        """

        print("[提示] 本次共保存 %d 道题" % total)
        for label, count in counts.items():
            print("    %s %d 道" % (label, count))
        if skipped:
            print("[提示] 下面这些题一屏放不下、被跳过了，需要手动补截：%s"
                  % "、".join(skipped))

    @staticmethod
    def probe():

        """
        调参用：截一张整屏，打印每张题卡的位置、题目编号和页脚题型（不滑动、不存图）
        """

        frame = AndroidDevice.capture()
        if frame is None:
            return

        print("整屏 %d x %d" % (frame.size[0], frame.size[1]))
        cards = QuestionCard.split(frame)
        if not cards:
            print("没识别到题目，检查画面是否停在试卷页面（标题行要有红色“（x分）”）")
            return

        for index, card in enumerate(cards, start=1):
            print("  第%d张题卡: 第%s题，题型 %s，题干 y=%d..%d，%s"
                  % (index, QuestionCard.header_number(frame, card),
                     QuestionCard.footer_type(frame, card), card.top, card.bottom,
                     "完整" if card.complete() else "被边缘切掉"))
