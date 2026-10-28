# ================================================================== #
# @Author: Fantasy_Silence                                           #
# @Time: 2026-10-29                                                  #
# @IDE: Visual Studio Code & PyCharm                                 #
# @Python: 3.9.7                                                     #
# ================================================================== #
# @Description: 自动截取数苑校园题目，一道题存一张图                   #
# ================================================================== #
import os
import time
import hashlib
import numpy as np
from typing import List, Literal, Optional, Tuple

from src.common import const
from src.common.figuresio import FiguresIO
from src.modules.tools.android_device import AndroidDevice
from src.modules.tools.emulator_screen import EmulatorScreen
from src.modules.tools.question_card import Card, QuestionCard


class GetScreenshot:

    """
    自动截取数苑校园题目

    流程：截整屏 -> 定位每道题 -> 用标题行的「题目N」当唯一键去重 -> 存图
          -> 把「第一道还没存下来的题」顶到目标位置 -> 再截整屏 ...

    几个关键点：

        1. 去重看题目编号，不再凭图像相似度——不同题目的版式往往一模一样，
           只比缩略图会把它们误判成同一题，静默丢题；
        2. 滑动对齐到「第一道未保存的题」，压顶的题会往回拉一点补回来；
        3. 连续几帧画面不动才判定到底，不会因为一次滑动被吞掉就提前结束；
        4. 文件名直接用题目编号（题目273 -> 273.png），和 txt、Word 对得上。
    """

    # ------ 连续多少帧画面不变，才认为真的到底 ------ #
    STILL_LIMIT = 3

    # ------ 比一屏还高的题，跳过时翻多少 ------ #
    TALL_RATIO = 0.75

    @staticmethod
    def figure_path(fig_name: str, sub_dir: Optional[str] = None) -> str:

        """
        图片的保存路径：给了 sub_dir 就存到 resources/row_pngs/子文件夹/
        传 "单选题" 就存到 resources/row_pngs/单选题/273.png
        """

        return FiguresIO.loadFigure(fig_name, sub_dir)

    @staticmethod
    def show_info():

        """
        打印当前用的是哪个通道，便于确认
        """

        if AndroidDevice.adb() is not None:
            print("截图/滑动: adb (%s)" % AndroidDevice.adb())
        else:
            left, top, width, height = EmulatorScreen.window_box()
            print("截图/滑动: 鼠标（虚拟机画面 %d, %d %d x %d，缩放 %.3f）"
                  % (left, top, width, height, EmulatorScreen.scale()))
            print("提醒：拖拽靠鼠标事件送达虚拟机，运行期间别让别的窗口挡住虚拟机画面")

    @staticmethod
    def probe():

        """
        调参用：存一张整屏，并打印识别到的题卡位置和题目编号
        """

        frame = AndroidDevice.capture()
        if frame is None:
            return

        path = GetScreenshot.figure_path(const.PROBE_FIGURE)
        frame.save(path)
        height = frame.size[1]
        print("整屏 %d x %d -> %s" % (frame.size[0], height, path))

        cards = QuestionCard.split(frame)
        if not cards:
            print("没识别到题目，检查画面是否停在试卷页面（标题行要有红色“（x分）”）")
            return
        for index, card in enumerate(cards, start=1):
            print("  第%d张题卡: 第%s题，题干 y=%d..%d，%s"
                  % (index, QuestionCard.header_number(frame, card), card.top, card.bottom,
                     "完整" if card.complete() else "被边缘切掉"))

    @staticmethod
    def already_saved(number, signature, saved_numbers, saved_images) -> bool:

        """
        这道题是不是已经存过了

        编号可靠时编号就是唯一键；编号读不出来才退回指纹比较（阈值更严）
        """

        if number is not None:
            return number in saved_numbers

        for saved in saved_images:
            if saved.shape != signature.shape:
                continue
            if float(np.logical_xor(saved, signature).mean()) < const.SAME_RATIO:
                return True
        return False

    @staticmethod
    def first_unsaved(frame, cards, numbers, saved_numbers, saved_images, skipped) -> Tuple[Optional[Card], Optional[int]]:

        """
        画面里第一道还没存下来的题（按编号跳过已存的、跳过的），没有就返回 (None, None)
        """

        for card, number in zip(cards, numbers):

            if number is not None:
                if number in saved_numbers or number in skipped:
                    continue
                return card, number

            # ------ 没读出编号：只能靠指纹判断存没存过 ------ #
            if not card.complete():
                return card, number
            signature = QuestionCard.fingerprint(QuestionCard.crop(frame, card))
            if GetScreenshot.already_saved(None, signature, saved_numbers, saved_images):
                continue
            return card, number

        return None, None

    @staticmethod
    def target_scroll(card: Card, height: int) -> int:

        """
        把这道题的标题行顶到目标位置要滑多少
        负数表示往回滑（题被顶部标题栏压住了，往回拉一点把它补回来）
        """

        scroll = card.header_top - const.TARGET_HEADER_TOP
        return max(-int(height * 0.5), min(scroll, int(height * 0.8)))

    @staticmethod
    def save(
        is_save: bool = True,
        png_type: Literal["单选题", "分析题", "计算题", "画图题"] = "单选题",
        pages: int = 3,
    ):

        """
        pages: 最多截几道题，每道题存一张图
        png_type: 题型，同时用作子文件夹名，比如 单选题 -> resources/row_pngs/单选题/
        从当前画面位置开始往下截，所以运行前先把试卷滑到最上面
        """

        if const.VERBOSE:
            GetScreenshot.show_info()

        # ------ 提示一下旧图，同名会被覆盖 ------ #
        folder = FiguresIO.loadFigure(sub_dir=png_type)
        olds = [name for name in os.listdir(folder) if name.endswith(".png")]
        if olds:
            print("[提示] %s 下已有 %d 张旧图，同名的会被覆盖" % (png_type, len(olds)))

        # ------ 睡5s，便于打开题目页面 ------ #
        time.sleep(5)

        saved_numbers: List[int] = []
        saved_images: List[np.ndarray] = []
        skipped: List[int] = []
        last_frame = None
        still = 0

        for _ in range(pages * 6 + 10):

            frame = AndroidDevice.capture()
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

                # ------ 编号明显倒退，多半是 OCR 认错了，当成没认出来 ------ #
                if number is not None and saved_numbers and number < saved_numbers[-1]:
                    print("[提示] 读到编号 %d，比上一题的 %d 还小，按未读出处理"
                          % (number, saved_numbers[-1]))
                    number = None

                image = QuestionCard.crop(frame, card)
                signature = QuestionCard.fingerprint(image)

                if GetScreenshot.already_saved(number, signature, saved_numbers, saved_images):
                    if number is not None:
                        print("跳过 第%d题：之前已经存过" % number)
                    continue

                if number is None:
                    index = (max(saved_numbers) + 1) if saved_numbers else 1
                    print("[警告] 有一题没读出编号，暂存为 %d.png" % index)
                else:
                    index = number
                    if saved_numbers and index != saved_numbers[-1] + 1:
                        print("[提示] 编号从 %d 直接跳到 %d，中间可能有题没截到"
                              % (saved_numbers[-1], index))

                saved_numbers.append(index)
                saved_images.append(signature)

                if is_save:
                    name = "%d.png" % index
                    image.save(GetScreenshot.figure_path(name, png_type))
                    print("已保存 %s\\%s (%d x %d)" % (png_type, name, image.size[0], image.size[1]))

                if len(saved_numbers) >= pages:
                    print("[提示] 已达到 pages=%d，停止" % pages)
                    return

            # ------ 下一道还没存的题就是目标，按它决定滑多少 ------ #
            target, target_number = GetScreenshot.first_unsaved(
                frame, cards, numbers, saved_numbers, saved_images, skipped
            )

            if target is None:
                scroll = int(height * 0.5)
            else:
                scroll = GetScreenshot.target_scroll(target, height)

                # ------ 已经在目标位置还是存不下来，说明这题一屏放不下 ------ #
                if abs(scroll) <= 20 and not target.complete():
                    if target_number is not None and target_number not in skipped:
                        skipped.append(target_number)
                        print("[提示] 第%s题一屏放不下，已跳过（可手动补截）" % target_number)
                    scroll = int(height * GetScreenshot.TALL_RATIO)

            # ------ 画面没变：先重试，连续几帧不动才认为到底 ------ #
            digest = hashlib.md5(frame.tobytes()).hexdigest()
            if digest == last_frame:
                still += 1
                if still >= GetScreenshot.STILL_LIMIT:
                    print("[提示] 连续 %d 帧画面没有变化，判定已经到底" % still)
                    break
                print("[提示] 画面没有变化，重试一次滑动")
                AndroidDevice.swipe(scroll if abs(scroll) > 60 else 450)
                time.sleep(1)
                continue

            still = 0
            last_frame = digest

            AndroidDevice.swipe(scroll)
            time.sleep(1)

        print("[提示] 结束：本次共保存 %d 道题" % len(saved_numbers))
        if skipped:
            print("[提示] 下面这些题一屏放不下、被跳过了，需要手动补截：%s"
                  % "、".join(str(number) for number in skipped))
