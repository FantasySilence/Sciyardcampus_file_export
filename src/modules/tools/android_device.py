# ================================================================== #
# @Author: Fantasy_Silence                                           #
# @Time: 2026-10-29                                                  #
# @IDE: Visual Studio Code & PyCharm                                 #
# @Python: 3.9.7                                                     #
# ================================================================== #
# @Description: 虚拟机读写：adb 截图 / 滑动，没有 adb 时退回鼠标        #
# ================================================================== #
import io
import os
import time
import shutil
import pyautogui
import subprocess
from PIL import Image
from typing import List, Optional, Tuple

from src.common import const
from src.modules.tools.emulator_screen import EmulatorScreen


class AndroidDevice:

    """
    和虚拟机打交道：截图、滑动

    两个通道：

        adb（优先）：screencap 拿到 1600*900 的原始画面，input swipe 直接在
                    虚拟机坐标里滑，不受窗口缩放 / 窗口遮挡 / DPI 影响，
                    出来的图也是原生分辨率，OCR 最清楚；
        鼠标（兜底）：没有 adb 时截虚拟机窗口 + 拖拽滑动，
                    要求运行期间虚拟机窗口在最前面、没被别的窗口挡住。
    """

    # ------ adb 探测结果的缓存 ------ #
    _adb: Optional[str] = None
    _adb_searched = False

    @staticmethod
    def adb() -> Optional[str]:

        """
        找 adb（PATH -> const.ADB_CANDIDATES），找不到就退回鼠标通道
        """

        if not AndroidDevice._adb_searched:
            AndroidDevice._adb_searched = True
            adb = shutil.which(const.ADB_PATH or "adb")
            if adb is None:
                for candidate in const.ADB_CANDIDATES:
                    if os.path.exists(candidate):
                        adb = candidate
                        break
            AndroidDevice._adb = adb
            if adb is None:
                print(
                    "[提示] 没找到 adb，改用鼠标截图 + 拖拽；想要更稳的 adb 通道，"
                    '把 const.ADB_PATH 填成 r"...\\shell\\adb.exe"'
                )
        return AndroidDevice._adb

    @staticmethod
    def command(*args: str) -> List[str]:

        """
        拼一条 adb 命令，多开时自动带上 -s 序列号
        """

        adb = [AndroidDevice.adb() or "adb"]
        if const.ADB_SERIAL:
            adb += ["-s", const.ADB_SERIAL]
        return adb + list(args)

    @staticmethod
    def capture() -> Optional[Image.Image]:

        """
        截一张虚拟机整屏画面：优先 adb，失败或没有 adb 时截虚拟机窗口
        """

        if AndroidDevice.adb() is not None:
            result = subprocess.run(
                AndroidDevice.command("exec-out", "screencap", "-p"),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            if result.returncode == 0 and result.stdout:
                return Image.open(io.BytesIO(result.stdout)).convert("RGB")
            print("[警告] adb 截图失败：%s，改用鼠标截图" % result.stderr.decode("utf-8", "ignore").strip())

        EmulatorScreen.enable_dpi_awareness()
        return pyautogui.screenshot(region=EmulatorScreen.window_box()).convert("RGB")

    @staticmethod
    def swipe(pixels: int):

        """
        翻页：pixels 是要滑动的虚拟机像素，正数向下、负数向上
        超过单次上限会自动拆成多段
        """

        for direction, step in AndroidDevice.chunks(pixels):
            if AndroidDevice.adb() is not None:
                AndroidDevice.adb_swipe(step, direction)
            else:
                AndroidDevice.drag(step, direction)
            time.sleep(0.4)

    @staticmethod
    def chunks(pixels: int) -> List[Tuple[int, int]]:

        """
        把一次滑动拆成不超过画面高度 60% 的若干段
        余数太小的尾段直接丢掉：几像素的滑动推不动页面，还会被当成"长按"选中文字
        """

        limit = int(const.EMULATOR_HEIGHT * const.MAX_SWIPE_RATIO)
        direction = 1 if pixels >= 0 else -1
        remaining = abs(int(pixels))

        steps = []
        while remaining > 0:
            step = min(remaining, limit)
            steps.append((direction, step))
            remaining -= step

        # ------ 去掉小尾巴（例如 542 拆成 540+2，那 2 像素没用还有风险） ------ #
        while len(steps) > 1 and steps[-1][1] < 40:
            steps.pop()
        return steps

    @staticmethod
    def start_point(direction: int) -> Tuple[int, int]:

        """
        按方向取滑动起点：向下翻页从靠近底部开始往上划，向上翻页反过来
        否则终点会被画面边界截短，实际滑不到要求的距离
        """

        x = int(const.EMULATOR_WIDTH * const.START_X_RATIO)
        ratio = const.START_Y_RATIO if direction > 0 else 1 - const.START_Y_RATIO
        return x, int(const.EMULATOR_HEIGHT * ratio)

    @staticmethod
    def duration_for(pixels: int) -> int:

        """
        按距离给滑动时长：短距离不能拖太久，否则 Android 当成"长按"，直接选中题干文字
        """

        duration = abs(int(pixels)) * const.ADB_MS_PER_PIXEL
        return max(const.ADB_MIN_DURATION, min(const.ADB_DURATION, duration))

    @staticmethod
    def adb_swipe(pixels: int, direction: int = 1, duration: Optional[int] = None):

        """
        adb shell input swipe 直接用虚拟机坐标，窗口怎么缩放都不影响
        """

        start_x, start_y = AndroidDevice.start_point(direction)
        end_y = max(10, min(start_y - direction * pixels, const.EMULATOR_HEIGHT - 10))

        if duration is None:
            duration = AndroidDevice.duration_for(end_y - start_y)

        subprocess.run(
            AndroidDevice.command(
                "shell", "input", "swipe",
                str(start_x), str(start_y), str(start_x), str(end_y),
                str(duration),
            ),
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        if const.VERBOSE:
            print("adb 滑动 %d 虚拟机像素，(%d, %d) => (%d, %d)，用时 %dms"
                  % (pixels, start_x, start_y, start_x, end_y, duration))

    @staticmethod
    def tap(x: int, y: int):

        """
        点一下（虚拟机坐标）：用来取消 WebView 的文本选中状态
        """

        if AndroidDevice.adb() is not None:
            subprocess.run(
                AndroidDevice.command("shell", "input", "tap", str(x), str(y)),
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            return

        screen_x, screen_y = EmulatorScreen.to_screen(x, y)
        pyautogui.click(screen_x, screen_y)

    @staticmethod
    def drag(pixels: int, direction: int = 1):

        """
        鼠标通道：在虚拟机坐标里划一条竖线，按住 -> 匀速拖动 -> 停顿 -> 松手
        pixels 会先按缩放比换算成屏幕像素再拖，所以虚拟机缩放多少都不影响结果
        """

        start_x_emu, start_y_emu = AndroidDevice.start_point(direction)
        end_y_emu = start_y_emu - direction * pixels

        # ------ 保证终点不会滑出画面 ------ #
        end_y_emu = max(10, min(end_y_emu, const.EMULATOR_HEIGHT - 10))

        start_x, start_y = EmulatorScreen.to_screen(start_x_emu, start_y_emu)
        end_x, end_y = EmulatorScreen.to_screen(start_x_emu, end_y_emu)

        # ------ 按下 ------ #
        pyautogui.moveTo(start_x, start_y, _pause=False)
        time.sleep(0.05)
        pyautogui.mouseDown(x=start_x, y=start_y, _pause=False)

        # ------ 分步移动：每 10 屏幕像素一个点，接近真实手指的匀速滑动 ------ #
        steps = max(8, abs(end_y - start_y) // 10)
        for index in range(1, steps + 1):
            ratio = index / steps
            pyautogui.moveTo(
                int(round(start_x + (end_x - start_x) * ratio)),
                int(round(start_y + (end_y - start_y) * ratio)),
                _pause=False,
            )
            time.sleep(const.DRAG_DURATION / steps)

        # ------ 停顿再松手，速度归零，页面不会继续惯性滑 ------ #
        time.sleep(const.HOLD_BEFORE_RELEASE)
        pyautogui.mouseUp(x=end_x, y=end_y, _pause=False)

        if const.VERBOSE:
            print(
                "拖拽 %d 虚拟机像素 -> 屏幕 %d 像素，(%d, %d) => (%d, %d)"
                % (pixels, abs(end_y - start_y), start_x, start_y, end_x, end_y)
            )
