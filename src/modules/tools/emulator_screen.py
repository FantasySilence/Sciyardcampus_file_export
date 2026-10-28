# ================================================================== #
# @Author: Fantasy_Silence                                           #
# @Time: 2026-10-29                                                  #
# @IDE: Visual Studio Code & PyCharm                                 #
# @Python: 3.9.7                                                     #
# ================================================================== #
# @Description: 虚拟机画面与电脑屏幕之间的坐标适配                     #
# ================================================================== #
import sys
import ctypes
from typing import Optional, Tuple

from src.common import const


class EmulatorScreen:

    """
    虚拟机画面 <-> 电脑屏幕坐标适配

    只有走鼠标通道（没有 adb）时才用得上：虚拟机是 1600*900，电脑屏幕是
    1920*1080，虚拟机窗口是被缩放后显示在屏幕上的，所以屏幕上的距离和
    虚拟机里的像素不是 1:1，必须靠缩放比换算，并且拖拽距离要按屏幕像素算。
    """

    # ------ 自动探测的缓存，(left, top, width, height) ------ #
    _detected_box: Optional[Tuple[int, int, int, int]] = None

    @staticmethod
    def enable_dpi_awareness():

        """
        Windows 缩放 125% / 150% 时，未声明 DPI 感知的进程会被系统虚拟化，
        pyautogui 拿到的屏幕尺寸、鼠标坐标和截图区域都会对不上，这里声明一下
        保证三者都是 1:1 的物理像素
        """

        if sys.platform != "win32" or not const.DPI_AWARE:
            return

        try:
            # ------ PROCESS_PER_MONITOR_DPI_AWARE ------ #
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                print("[警告] 无法开启 DPI 感知，若显示器缩放不是 100%，拖拽距离会偏小")

    @staticmethod
    def window_box() -> Tuple[int, int, int, int]:

        """
        取虚拟机画面在屏幕上的位置和大小，(left, top, width, height)
        只包含画面本身，不含标题栏和边框
        """

        # ------ 手动指定优先 ------ #
        if const.WINDOW_BOX is not None:
            return tuple(const.WINDOW_BOX)

        # ------ 自动探测只做一次，后面都用缓存 ------ #
        if EmulatorScreen._detected_box is not None:
            return EmulatorScreen._detected_box

        # ------ 自动探测：按标题找窗口，再按 1600:900 的宽高比裁出画面 ------ #
        try:
            import pygetwindow as gw
        except ImportError:
            raise RuntimeError(
                "缺少 pygetwindow，请先 pip install PyGetWindow，"
                "或把 const.WINDOW_BOX 手动填成 (left, top, width, height)"
            )

        candidates = []
        for window in gw.getAllWindows():
            title = (window.title or "").strip()
            if not title:
                continue
            # ------ 指定了标题就只认这个窗口 ------ #
            if const.WINDOW_TITLE is not None:
                if title != const.WINDOW_TITLE:
                    continue
            elif not any(keyword.lower() in title.lower() for keyword in const.WINDOW_TITLE_KEYWORDS):
                continue
            if getattr(window, "isMinimized", False) or not getattr(window, "visible", True):
                continue

            width, height = window.width, window.height
            if width <= 0 or height <= 0:
                continue
            # ------ 太小的小窗（工具栏、悬浮窗）直接跳过 ------ #
            if width < 200 or height < 150:
                continue

            # ------ 宽高比越接近 16:9、面积越大的窗口，越可能是画面窗口 ------ #
            aspect_error = abs(width / height - const.EMULATOR_WIDTH / const.EMULATOR_HEIGHT)
            candidates.append((aspect_error, -width * height, window))

        if not candidates:
            raise RuntimeError(
                "没有找到虚拟机窗口，请把 const.WINDOW_BOX 手动填成 (left, top, width, height)"
            )

        candidates.sort(key=lambda item: (item[0], item[1]))
        window = candidates[0][2]

        # ------ 优先用 Win32 客户区，精确排除标题栏和边框 ------ #
        client = EmulatorScreen.client_box(window)
        if client is None:
            client = (window.left, window.top, window.width, window.height)
        client_left, client_top, client_width, client_height = client

        # ------ 客户区不一定正好是 16:9，按比例居中取中间的渲染区 ------ #
        scale = min(client_width / const.EMULATOR_WIDTH, client_height / const.EMULATOR_HEIGHT)
        render_width = int(round(const.EMULATOR_WIDTH * scale))
        render_height = int(round(const.EMULATOR_HEIGHT * scale))
        left = client_left + (client_width - render_width) // 2
        top = client_top + (client_height - render_height) // 2

        EmulatorScreen._detected_box = (int(left), int(top), render_width, render_height)
        return EmulatorScreen._detected_box

    @staticmethod
    def client_box(window) -> Optional[Tuple[int, int, int, int]]:

        """
        取窗口的客户区（不含标题栏、边框）在屏幕上的位置和大小
        拿不到窗口句柄时返回 None，调用方会退回按 16:9 估算
        """

        if sys.platform != "win32":
            return None

        hwnd = getattr(window, "_hWnd", None)
        if not hwnd:
            return None

        try:
            from ctypes import wintypes

            rect = wintypes.RECT()
            point = wintypes.POINT(0, 0)
            # ------ GetClientRect 得到客户区大小，ClientToScreen 把 (0,0) 换成屏幕坐标 ------ #
            ctypes.windll.user32.GetClientRect(hwnd, ctypes.byref(rect))
            ctypes.windll.user32.ClientToScreen(hwnd, ctypes.byref(point))
        except Exception:
            return None

        width = int(rect.right - rect.left)
        height = int(rect.bottom - rect.top)
        if width <= 0 or height <= 0:
            return None
        return int(point.x), int(point.y), width, height

    @staticmethod
    def scale() -> float:

        """
        虚拟机像素 -> 屏幕像素 的缩放比
        例如窗口画面是 1280*720，缩放比就是 0.8，滑 700 虚拟机像素只需拖 560 屏幕像素
        """

        _, _, width, height = EmulatorScreen.window_box()
        return min(width / const.EMULATOR_WIDTH, height / const.EMULATOR_HEIGHT)

    @staticmethod
    def to_screen(x: float, y: float) -> Tuple[int, int]:

        """
        虚拟机坐标 -> 屏幕坐标
        """

        left, top, _, _ = EmulatorScreen.window_box()
        scale = EmulatorScreen.scale()
        return int(round(left + x * scale)), int(round(top + y * scale))
