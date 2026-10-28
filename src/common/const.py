# ================================================================== #
# @Author: Fantasy_Silence                                           #
# @Time: 2026-10-29                                                  #
# @IDE: Visual Studio Code & PyCharm                                 #
# @Python: 3.9.7                                                     #
# ================================================================== #
# @Description: 全项目共用的常量与可调参数，需要微调时改这里即可         #
# ================================================================== #

# ------ 虚拟机逻辑分辨率（模拟器设置里填的分辨率） ------ #
EMULATOR_WIDTH = 1600
EMULATOR_HEIGHT = 900

# ------ 是否打印过程信息 ------ #
VERBOSE = True

# ------ 虚拟机窗口：自动探测的关键字，以及手动指定 ------ #
# 模拟器开了多个窗口（启动器 + 画面）时自动探测可能挑错，
# 这时把 WINDOW_TITLE 填成确切标题，或者直接填 WINDOW_BOX = (left, top, width, height)
WINDOW_TITLE_KEYWORDS = ("MuMu", "Android", "Emulator", "模拟器", "夜神", "雷电", "BlueStacks")
WINDOW_TITLE = None
WINDOW_BOX = None

# ------ Windows 缩放不是 100% 时必须开 DPI 感知 ------ #
DPI_AWARE = True

# ------ adb 通道 ------ #
# PATH 里找不到 adb 时按顺序试 ADB_CANDIDATES
ADB_PATH = None
ADB_SERIAL = None
ADB_CANDIDATES = (
    # MuMu 模拟器 adb 路径
    r"D:\BlueStacks_nxt_cn\MuMuPlayer\nx_device\15.0\shell\adb.exe",
    r"C:\Program Files\Netease\MuMuPlayer-12.0\shell\adb.exe",
)

# ------ input swipe 的时长(ms) ------ #
# MuMu实测：500ms 滑 450 像素，松手速度太快，WebView 会继续惯性滑好几屏；
#          1500ms 以上时滑多少就是多少（450 像素实测位移 451）
ADB_DURATION = 1500

# ------ 鼠标拖拽参数（没有 adb 时用） ------ #
DRAG_DURATION = 0.45          # 一次拖拽的时长（秒），太短会被识别成"甩"
HOLD_BEFORE_RELEASE = 0.2     # 松手前的停顿（秒），让虚拟机的速度跟踪归零
MAX_SWIPE_RATIO = 0.6         # 单次最多滑过画面高度的多少
START_X_RATIO = 0.5           # 滑动起点：横向中间
START_Y_RATIO = 0.8           # 滑动起点：纵向 80%（避开状态栏和底部导航栏）

# ------ 题卡构图 ------ #
CARD_TOP_MARGIN = 30
CARD_BOTTOM_MARGIN = 52

# ------ 题卡识别阈值 ------ #
CARD_RED = (200, 80, 80)      # 标题行"（x分）"红字：R > 200 且 G、B < 80
CARD_DARK_LUM = 140           # 正文亮度上限（页脚灰字在 175 以上）
CARD_FOOTER_LUM = 165         # 页脚灰字亮度下限
CARD_FOOTER_WIDTH = 500       # 只在画面左侧这么多像素里找页脚，避开滚动条
CARD_FOOTER_MIN = 6           # 页脚文字行至少多少像素高（滤掉抗锯齿的假页脚）
CARD_SAFE_TOP = 130           # 顶部被 App 标题栏（状态栏 + "试卷预览"）遮住的高度，
                              # 题干落在这条线以上就说明这题被切了，要等下一屏

# ------ 题卡去重指纹 ------ #
# 缩略图大小、"有字"的亮度阈值，以及判定为同一道题的差异像素比例
# （MuMu实测：同一道题错开 1~3 像素时 0.003~0.009，不同题之间 0.021~0.037）
THUMB_SIZE = (200, 60)
THUMB_INK_LUM = 170
SAME_RATIO = 0.015

# ------ 截图流程 ------ #
TARGET_HEADER_TOP = 220       # 滑动后希望下一题标题行停在的纵向位置
PROBE_FIGURE = "_probe.png"   # probe() 保存整屏画面的文件名

# ------ 文字提取（OCR） ------ #
# Tesseract 5.1，语言包有 chi_sim / eng / equ
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
TESSERACT_LANG = "chi_sim+eng"   # 中文简体 + 英文数字
TESSERACT_CONFIG = "--psm 6"     # 当成一整块文字，适合题目卡片
OCR_SCALE = 1                    # 放大倍数：实测 1 倍最稳，加大反而会把正文认错
OCR_FORMULA_SUFFIX = "_formula"  # 含公式的题在文件名上标注：1_formula.txt

# ------ 生成 Word ------ #
WORD_FONT = "宋体"               # 正文中文字体
WORD_FONT_SIZE = 10.5            # 五号
WORD_TITLE_SUFFIX = "题库"        # 文件名：选择题题库.docx
WORD_QUESTION_TITLE = "第%d题"    # 每题前面的小标题

