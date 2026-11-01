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

在项目根目录执行 python main.py，进入交互式菜单，按数字选择要做的事：

    1) 整卷：采集 + 文字 + Word + 核对     # 一条龙，跑完自动统计
    2) 整卷：只采集                        # 混合题型，一次滚到底
    3) 单题型：采集                        # 选择题 / 分析题 / 画图题 / 计算题 / 全部依次
    4) 文字提取（OCR）                     # 全部题型 / 指定题型 / 某一卷
    5) 导出 Word                           # 全部题型 / 指定题型 / 某一卷
    6) 检查产物                            # 分题型 + 每一卷的图片 / txt / Word 数量
    7) 调试：看当前画面的切题结果           # 截一张、打印题卡位置与题号，不滑动、不改数据
    0) 退出

约定：

- 采集前要先把模拟器里的试卷滑到对应位置，菜单会停下来等回车（q 取消）；
- 题量上限默认 const.DEFAULT_PAGES（10），直接回车就用默认值，也可以手动输入；
- 输入 0 返回上一级，主菜单再输 0 退出；Ctrl+C 只取消当前操作，不会退出程序。

具体实现在 src/modules/interactions/ 下：菜单项流程在 Menus，终端输入在 Console，
动作在 Actions，产物统计在 Status。
"""

from src.modules.interactions.console import Console
from src.modules.interactions.status import Status
from src.modules.interactions.menus import Menus


def start():

    """
    交互式主菜单：一直循环，直到选 0 或按 Ctrl+C
    """

    while True:

        Status.banner()
        print()
        Menus.show()

        try:
            key = Console.ask_key(list(Menus.KEYS))
        except (KeyboardInterrupt, EOFError):
            print("\n已退出")
            return

        if key is None:
            print("已退出")
            return

        try:
            Menus.run(key)
        except (KeyboardInterrupt, EOFError):
            print("\n[提示] 已取消当前操作，返回主菜单")
            print("[提示] 如果模拟器还停在滑动中途，先点一下画面再重试")
        except RuntimeError as error:
            # ------ 模拟器没开、adb 没连上、Tesseract 没装这类，都抛 RuntimeError ------ #
            print("\n[错误] %s" % error)
            print("[提示] 截图需要模拟器开着并连上 adb：先执行 adb connect 127.0.0.1:16384；")
            print("       OCR 需要 Tesseract，确认 const.TESSERACT_PATH 指向 tesseract.exe")
            Console.pause()


if __name__ == "__main__":

    start()
