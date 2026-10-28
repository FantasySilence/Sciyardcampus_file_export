# ================================================================== #
# @Author: Fantasy_Silence                                           #
# @Time: 2026-10-29                                                  #
# @IDE: Visual Studio Code & PyCharm                                 #
# @Python: 3.9.7                                                     #
# ================================================================== #
# @Description: 自动截取数苑校园题目，一道题存一张图                   #
# ================================================================== #
import time
import hashlib
import numpy as np
from typing import List, Literal, Optional

from src.common import const
from src.common.figuresio import FiguresIO
from src.modules.tools.android_device import AndroidDevice
from src.modules.tools.emulator_screen import EmulatorScreen
from src.modules.tools.question_card import Card, QuestionCard


class GetScreenshot:

    """
    自动截取数苑校园题目，用于文字提取流程是：

        截整屏 -> 按红色"（x分）"定位每道题 -> 切出题干和选项 -> 存图
        -> 把下一道没露全的题顶到画面靠上的位置 -> 再截整屏 ...

    每屏都会重新识别题目位置，滑动距离即使有偏差也不会错位，
    重复截到的同一道题会被指纹去重。
    """

    @staticmethod
    def figure_path(fig_name: str, sub_dir: Optional[str] = None) -> str:

        """
        图片的保存路径：给了 sub_dir 就存到 resources/row_pngs/子文件夹/ 
        下传 "单选题" 就存到 resources/row_pngs/单选题/1.png
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
        调参用：存一张整屏，并打印识别到的题卡位置，确认切题对不对
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
            print("  第%d张题卡: 题干 y=%d..%d，%s"
                  % (index, card.top, card.bottom, "完整" if card.complete() else "被边缘切掉"))

    @staticmethod
    def next_scroll(cards: List[Card], height: int) -> int:

        """
        下一次滑多少：把画面底部那道没露全的题顶到目标位置
        滑动距离跟着真实题目高度走，所以不会像固定步长那样把题漏掉
        """

        for card in cards:

            if not card.cut_bottom():
                continue

            scroll = card.header_top - const.TARGET_HEADER_TOP
            if scroll > 20 or scroll < -20:
                return scroll

            # ------ 标题已经贴到目标位置还是露不全，说明这题一屏放不下 ------ #
            print("[提示] y=%d 处的题目一屏放不下，先往下翻一屏" % card.header_top)
            return int(height * 0.75)

        # ------ 画面里没有半截的题，就翻半屏找下一道 ------ #
        return int(height * 0.5)

    @staticmethod
    def repeated(signature: np.ndarray, history: List[np.ndarray]) -> bool:

        """
        这张题卡是不是之前已经截过了
        """

        for saved in history:
            if saved.shape != signature.shape:
                continue
            if float(np.logical_xor(saved, signature).mean()) < const.SAME_RATIO:
                return True
        return False

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

        # ------ 睡5s，便于打开题目页面 ------ #
        time.sleep(5)

        saved_images: List[np.ndarray] = []
        last_frame = None

        for _ in range(pages * 4 + 4):

            frame = AndroidDevice.capture()
            if frame is None:
                return

            height = frame.size[1]
            cards = QuestionCard.split(frame)
            if not cards:
                print("[错误] 没识别到题目，检查画面是否停在试卷页面（标题行要有红色“（x分）”）")
                return

            # ------ 把这一屏里完整露出来的题都存下来 ------ #
            for card in cards:

                if not card.complete():
                    continue

                image = QuestionCard.crop(frame, card)
                signature = QuestionCard.fingerprint(image)
                if GetScreenshot.repeated(signature, saved_images):
                    continue

                saved_images.append(signature)
                if is_save:
                    # ------ 每道题存一张图：resources/row_pngs/单选题/1.png、2.png ... ------ #
                    name = "%d.png" % len(saved_images)
                    image.save(GetScreenshot.figure_path(name, png_type))
                    print("已保存 %s\\%s (%d x %d)" % (png_type, name, image.size[0], image.size[1]))

                if len(saved_images) >= pages:
                    return

            # ------ 画面一直没变就是到底了 ------ #
            signature = hashlib.md5(frame.tobytes()).hexdigest()
            if signature == last_frame:
                print("[提示] 页面滑不动了，可能已经到试卷末尾")
                return
            last_frame = signature

            AndroidDevice.swipe(GetScreenshot.next_scroll(cards, height))
            time.sleep(1)

        print("[提示] 只截到 %d 道题" % len(saved_images))
