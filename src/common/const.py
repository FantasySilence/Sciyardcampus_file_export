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
# 另外：短距离 + 长时长会被 Android 当成"长按"，直接选中题干文字，
#      所以时长按距离缩放，并且不低于 ADB_MIN_DURATION
ADB_DURATION = 1500
ADB_MIN_DURATION = 300
ADB_MS_PER_PIXEL = 3          # 每滑 1 像素给多少毫秒

# ------ 鼠标拖拽参数（没有 adb 时用） ------ #
DRAG_DURATION = 0.45          # 一次拖拽的时长（秒），太短会被识别成"甩"
HOLD_BEFORE_RELEASE = 0.2     # 松手前的停顿（秒），让虚拟机的速度跟踪归零
MAX_SWIPE_RATIO = 0.6         # 单次最多滑过画面高度的多少
START_X_RATIO = 0.5           # 滑动起点：横向中间
START_Y_RATIO = 0.8           # 滑动起点：纵向 80%（避开状态栏和底部导航栏）

# ------ 题卡构图 ------ #
CARD_TOP_MARGIN = 30
CARD_BOTTOM_MARGIN = 52
CARD_FOOTER_GAP = 10          # 裁图下沿和页脚之间至少留多少像素，别把页脚裁进来

# ------ 题卡识别阈值 ------ #
CARD_RED = (200, 80, 80)      # 标题行"（x分）"红字：R > 200 且 G、B < 80
CARD_DARK_LUM = 140           # 正文亮度上限（页脚灰字在 175 以上）
CARD_FOOTER_LUM = 165         # 页脚灰字亮度下限
CARD_FOOTER_WIDTH = 500       # 只在画面左侧这么多像素里找页脚，避开滚动条
CARD_FOOTER_MIN = 6           # 页脚文字行至少多少像素高（滤掉抗锯齿的假页脚）
CARD_SAFE_TOP = 130           # 顶部被 App 标题栏（状态栏 + "试卷预览"）遮住的高度，
                              # 题干落在这条线以上就说明这题被切了，要等下一屏

# ------ 题卡去重指纹 ------ #
# 正常情况按标题行的"题目N"去重，只有编号读不出来时才退回这个指纹比较。
# 阈值取严一些：实测同一道题错开 1~3 像素时差异 0.003~0.009，
# 而版式相同、文字不同的两道题也可能低到 0.0106，所以卡在 0.008 更安全。
THUMB_SIZE = (200, 60)
THUMB_INK_LUM = 170
SAME_RATIO = 0.008

# ------ 截图流程 ------ #
TARGET_HEADER_TOP = 220       # 滑动后希望下一题标题行停在的纵向位置
PROBE_FIGURE = "_probe.png"   # probe() 保存整屏画面的文件名

# ------ 文本选中检测 ------ #
# WebView 里长按文字会进入选词状态（整页蓝底 + 复制/全选菜单），一旦发生就截不了图。
# 这里用蓝色像素占比判断，超过阈值就点一下空白处取消。
SELECTION_RATIO = 0.003
SELECTION_TAP = (1550, 450)   # 取消选中时点一下的位置（画面右侧空白处）

# ------ 文字提取（OCR） ------ #
# Tesseract 5.1，语言包有 chi_sim / eng / equ
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
TESSERACT_LANG = "chi_sim+eng"   # 中文简体 + 英文数字
TESSERACT_CONFIG = "--psm 6"     # 当成一整块文字，适合题目卡片
OCR_SCALE = 1                    # 放大倍数：实测 1 倍最稳，加大反而会把正文认错
OCR_FORMULA_SUFFIX = "_formula"  # 含公式的题在文件名上标注：1_formula.txt
OCR_TABLE_SUFFIX = "_table"      # 含表格的题：1_table.txt
OCR_IMAGE_SUFFIX = "_image"      # 含图像（图形）的题：1_image.txt

# 一道题同时有多个特征时按这个顺序拼：1_formula_table.txt
OCR_KIND_SUFFIX = {
    "formula": OCR_FORMULA_SUFFIX,
    "table": OCR_TABLE_SUFFIX,
    "image": OCR_IMAGE_SUFFIX,
}
OCR_KIND_ORDER = ("formula", "table", "image")

# ------ 题卡"长相"判断（表格 / 图像） ------ #
# 表格：几条贯穿全宽的横线 + 几条贯穿大半高的竖线；
# 图像：连续一大片行都有墨迹（正常文字行之间一定有空行）。
# 阈值是按 1600 宽的题卡标定的，换分辨率要跟着改。
SHAPE_DARK_LUM = 160            # 比这个亮度更暗的像素算"有内容"
SHAPE_TABLE_H_RATIO = 0.18      # 横线至少占画面宽度的比例
SHAPE_TABLE_H_MIN = 120         # 横线最短长度（像素）
SHAPE_TABLE_V_RATIO = 0.12      # 竖线至少占画面高度的比例
SHAPE_TABLE_V_MIN = 60          # 竖线最短长度（像素）
SHAPE_TABLE_H_LINES = 3         # 至少几条长横线才算表格
SHAPE_TABLE_V_LINES = 3         # 至少几条长竖线才算表格
SHAPE_FIGURE_SPAN = 100         # 连续这么多行都有墨迹才算图像
SHAPE_LINE_GAP = 3              # 找长直线前，先补齐几像素的缝（表格格子之间会有缝）

# ------ 生成 Word ------ #
WORD_FONT = "宋体"               # 正文中文字体
WORD_FONT_SIZE = 10.5            # 五号
WORD_TITLE_SUFFIX = "题库"        # 文件名：选择题题库.docx
WORD_QUESTION_TITLE = "第%d题"    # 每题前面的小标题

