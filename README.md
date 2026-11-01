# Sciyardcampus_file_export

把「数苑校园」试卷预览里的题目，从安卓模拟器批量导出成本地题库：

**自动截图 → OCR 识别成文字 → 按题型生成 Word**，方便离线整理、复习和二次加工。

- 题目按题型分目录存放，截图与文字一一对应（`1.png` ↔ `1.txt`）
- 含数学公式的题会被标记出来（`1_formula.txt`），Word 里直接贴题目原图，避免公式被 OCR 认错
- 只适配 1600×900 的模拟器画面，开启模拟器后需要设置，走 adb 直连，不受窗口缩放、窗口遮挡影响
- 全部可调参数集中在 [`src/common/const.py`](src/common/const.py)

> 推荐的安卓模拟器：[MuMu 模拟器](https://mumu.163.com/)（详见「[模拟器配置](#模拟器配置推荐-mumu)」）

---

## 目录

- [工作流程](#工作流程)
- [环境要求](#环境要求)
- [安装](#安装)
- [模拟器配置（推荐 MuMu）](#模拟器配置推荐-mumu)
- [快速开始](#快速开始)
- [输出说明](#输出说明)
- [配置说明](#配置说明)
- [常见问题](#常见问题)
- [开发者指南](#开发者指南)
- [已知限制](#已知限制)
- [许可证](#许可证)

---

## 工作流程

```
安卓模拟器（MuMu，1600×900）
        │  adb screencap / input swipe
        ▼
① 截图  逐题识别、裁剪  ──►  resources/row_pngs/<题型>/N.png
        │
        │  Tesseract（chi_sim + eng）
        ▼
② 文字  分段落整理、公式标记 ──►  resources/row_txt/<题型>/N.txt
                                   resources/row_txt/<题型>/N_formula.txt
        │
        │  python-docx
        ▼
③ Word  有公式贴原图 / 无公式转正文 ──►  resources/word_output/<题型>题库.docx
```

三个步骤互相独立，可以分开反复跑：截图依赖模拟器，OCR 和 Word 只读写本地文件。

> 另有一条「**混合试卷**」路线：一份卷子里好几类题型混在一起时不用分次截——从最上面一次滚到底，
> 图存到 `resources/row_paper/<卷名>/pngs/`，文件名是顺序号（`1.png`、`2.png` …）。
> 见 [混合试卷（整卷一次截完）](#混合试卷整卷一次截完)。这条路**截图 → 文字 → Word** 都能跑。

**截图是怎么定题的**（不依赖固定坐标）：

1. 用标题行里的红字「（x分）」定位每道题的起点；
2. 用浅灰页脚「单选题 | 易 … 共享试题」判断这道题在画面里是否完整；
3. 深色正文的首尾就是题干第一行和最后一行选项，上下各留一点白裁出来；
4. 用标题行的「题目N」当唯一键去重，并把「第一道还没保存的题」顶到画面固定位置，
   所以题目高矮不齐也不会错位或漏题；文件名直接就是题目编号（`273.png`）。

**文字是怎么处理的**：

- 按「题干 / 每个选项 / 每个小问」合并成段落，段与段之间空一行；
- 公式片段统一用 `$...$` 包起来（后续交给 pandoc / Word 就是公式对象）；
- 每道题按内容特征打标签，写在 txt 文件名上，和纯文字题目区分开：

  | 标签 | 判据 | 例子 |
  |---|---|---|
  | `_formula` | OCR 出来的文字里有公式 | `1_formula.txt` |
  | `_table` | 版面里有成组的贯穿长横线 + 长竖线（表格边框） | `1_table.txt` |
  | `_image` | 连续一大片行都有墨迹（文字行之间必有空行，所以是插图） | `1_image.txt` |
  | （无） | 纯文字 | `1.txt` |

  一道题同时命中多个时按 `formula` → `table` → `image` 拼接，例如 `436_formula_table.txt`。

---

## 环境要求

| 项目 | 要求 |
|---|---|
| 操作系统 | Windows 10 / 11（代码用到了 Win32 接口：DPI 感知、读取窗口客户区） |
| Python | 3.9.7（开发时用的 `.venv`，克隆后需自行创建） |
| 模拟器 | 推荐 **MuMu 模拟器 12**，画面分辨率 **1600×900**、DPI 240、横屏 |
| OCR | Tesseract 5.x，需要 `chi_sim`、`eng` 语言包 |
| 依赖 | 见 [`reqiurements.txt`](reqiurements.txt)（`pytesseract`、`PyAutoGUI`、`PyGetWindow`、`numpy`、`pillow`、`python-docx`、`lxml`、`pywin32`） |

`adb` 不用单独装：MuMu 自带一份，脚本会自动去常见位置找（见下方配置）。

## 安装

```bash
git clone git@github.com:FantasySilence/Sciyardcampus_file_export.git
cd Sciyardcampus_file_export

# 0. 建虚拟环境（.venv 不进版本库）
python -m venv .venv

# 1. 依赖
.venv\Scripts\python.exe -m pip install -r reqiurements.txt

# 2. Tesseract：装 UB-Mannheim 版本，安装时勾选 Chinese (Simplified)
#    https://github.com/UB-Mannheim/tesseract/wiki
#    装完确认 src/common/const.py 里的 TESSERACT_PATH 指向 tesseract.exe
```

> 用 Notebook 的话，把 Jupyter 内核指到这个 `.venv`（`main.ipynb` 里记录的内核名是 `.venv (3.9.7)`）。

自检（截一张整屏，打印识别到的题卡位置和题目编号，不改动任何数据）：

```bash
python main.py
# 进菜单后选 7) 调试：看当前画面的切题结果
```

> 只会在 `resources/row_pngs/` 下多存一张 `_probe.png`，方便对照着看切题准不准。

---

## 模拟器配置（推荐 MuMu）

1. 安装 [MuMu 模拟器 12](https://mumu.163.com/)；
2. 打开模拟器设置 → 显示，把分辨率设为 **1600×900**、DPI **240**（横屏）；
3. 在模拟器里登录「数苑校园」，打开「试卷预览」，把试卷滑到**某个题型的开头**；
4. `adb` 保持默认（MuMu 自带，无需额外配置）；脚本会依次尝试：
   - `PATH` 里的 `adb`
   - `const.ADB_CANDIDATES` 里的 MuMu 常见路径（如 `…\MuMuPlayer\nx_device\15.0\shell\adb.exe`）

> **每次重启虚拟机后**，adb 里的设备连接会失效，截图会失败——先执行一次 `adb connect 127.0.0.1:16384`。
> 细节见[常见问题](#常见问题)里的「虚拟机重启后截图失败」。

**为什么推荐 MuMu**

- 自带 `adb`，不用再装 Android SDK；
- 走 adb 截图和滑动，**窗口缩放、被其他窗口遮住都不影响**，截图还是原生 1600×900；
- 分辨率、DPI 可自由设置，多开也兼容。

**换别的模拟器（夜神 / 雷电 / BlueStacks）**

- 有 adb 就行：把 `const.ADB_PATH` 指向它的 `adb.exe`；
- 没有 adb 时走鼠标兜底，需要让脚本认得出窗口：
  - 改 `const.WINDOW_TITLE_KEYWORDS`（标题关键字）或 `const.WINDOW_TITLE`（精确标题）；
  - 认不准时直接填 `const.WINDOW_BOX = (left, top, width, height)`；
  - 鼠标兜底期间不要让其他窗口挡住模拟器画面。

---

## 快速开始

### 方式一：交互菜单（`main.py`）

```bash
python main.py
```

进来先看到一屏状态（截图通道、各题型已有多少张图、每一卷的图 / txt / Word），然后按数字选：

```
==============================================================
 数苑校园试卷提取
 截图通道：adb
--------------------------------------------------------------
 分题型：分析题 78 · 画图题 84 · 计算题 136 · 选择题 567
 整卷：  期中卷（图 23 / txt 23 / Word 已生成）
==============================================================

  1) 整卷：采集 + 文字 + Word + 核对
  2) 整卷：只采集
  3) 单题型：采集
  4) 文字提取（OCR）
  5) 导出 Word
  6) 检查产物
  7) 调试：看当前画面的切题结果
  0) 退出

请选择：
```

| 选项 | 做什么 | 会问你什么 |
|---|---|---|
| 1 | 整卷一条龙：采集 → 文字 → Word → 核对 | 卷名、题量 |
| 2 | 整卷只采集 | 卷名、题量 |
| 3 | 单题型采集（可选连 OCR + Word） | 题型（含「全部依次」）、题量，采完问要不要继续 OCR / Word |
| 4 | 文字提取 | 范围：全部题型 / 指定题型 / 某一卷 |
| 5 | 导出 Word | 同上 |
| 6 | 检查产物 | — |
| 7 | 调试：截一张、打印题卡位置和题目编号 | — |

约定：

- **题量默认 10**：直接回车就用 10，也可以手动输入（整卷题多，记得给大一点，比如 200）；
- 采集前程序会停下，等你把模拟器里的试卷滑到对应位置再回车；输入 `q` 取消；
- 卷名可以直接输入新的，直接回车就沿用上一次用过的卷名；已有卷子会先列出来；
- 输入 `0` 返回上一级，主菜单再输 `0` 退出；`Ctrl+C` 只取消当前操作，不会退出程序；
- 开着中文输入法也能按数字（全角 `１` 等同于 `1`）。

题型列表与顺序写在 [`src/common/const.py`](src/common/const.py) 的 `PNG_TYPES` 里，按自己的试卷改即可。

> 题量上限截到数额就会停，日志里会提示 `已达到 pages=N`；整卷题多时记得给够。

> 截图过程会实时打印「已保存 选择题\273.png」「编号从 273 直接跳到 275，中间可能有题没截到」
> 这类信息，跑完还会汇总保存数量和跳过的题号，方便对照检查。

### 混合试卷（整卷一次截完）

一份卷子里选择题、分析题、计算题混在一起时，不用分次截，也不用手动滑到每个题型的开头：

```
python main.py
# 1) 整卷：采集 + 文字 + Word + 核对   ← 一条龙（推荐，跑完自动统计）
# 2) 整卷：只采集                      ← 只截图，之后用 4 / 5 单独做
```

选 1 之后只要回答两个问题：卷名（回车沿用上次的）、题量（回车=10，整卷记得给大）；

两步/三步分着跑也行，卷名填同一个即可，产物都落在这一卷自己的目录里：

```
① 采集     -> row_paper/期中卷/pngs/1.png …
② 文字提取 -> row_paper/期中卷/txts/1.txt …      （菜单 4，选「某一卷」）
③ 导出 Word -> word_output/期中卷.docx           （菜单 5，选「某一卷」）
```

也可以直接在 py 文件里调：

```python
from src.modules.datapreparation.paper_screenshot import GetPaperScreenshot

GetPaperScreenshot.probe()                                   # 先看题卡和页脚题型认得对不对
GetPaperScreenshot.save(paper="期中卷", pages=2000)
```

和分题型截图只有两处不同：

| | 分题型（菜单 3） | 混合试卷（菜单 1 / 2） |
|---|---|---|
| 文件名 | 题目编号（`273.png`） | **顺序号**（`1.png`、`2.png` …） |
| 目录 | `row_pngs/<题型>/` | `row_paper/<卷名>/pngs/` |
| 去重键 | 题目编号 | **(分区, 题目编号)**——整卷里每类题型的题号都从 1 开始，靠页脚的题型名把两段隔开 |
| 题型切换 | 手动，每段前回车 | 自动，读到题号回退时读页脚确认 |

滚动对齐、到底判定、防「长按选中题干」这些和分题型完全共用一套逻辑。

> `pages` 是题量上限：截到底会自己停，但给太小会提前结束。整卷跑记得手动给大（默认 10）。

截完之后提取文字，思路和分题型完全一样（分段、公式标 `$...$`、公式/表格/图像打标签），
只是读写目录换成卷子自己的（菜单 4 → 选「某一卷」）：
```python
from src.modules.datapreparation.paper_text_extraction import PaperTextExtraction

PaperTextExtraction.save(paper="期中卷")              # 全部
PaperTextExtraction.save(paper="期中卷", indexes=[1, 2])  # 只识别某几张
```

```
row_paper/期中卷/
├── pngs/   1.png  2.png  …
└── txts/   1.txt  1_formula.txt  2.txt  …     文件名与图片的顺序号一一对应
```

同一道题换标签重跑时，旧标签的 txt 会被删掉（`1_table.txt` → 跑成 `1.txt` 后不会并存）。
`txts` 里带标签的题同样会在结束时列出来，提示对着原图核对。

最后导出 Word（菜单 5 → 选「某一卷」），文件名就是卷名：
```python
from src.modules.process.paper_word_builder import PaperWordBuilder

PaperWordBuilder.save(paper="期中卷")
```

规则和分题型一致：带 `_formula` / `_table` / `_image` 的题贴原图，纯文字题转成正文，
每道题前面带「第N题」（N 就是图片的顺序号）。

菜单 6) 检查产物 也会按卷统计：

```
混合试卷：
  期中卷：图片 23 张，txt 23 份（公式 8、表格 0、图像 0），Word 已生成
```

### 方式二：Notebook（`main.ipynb`）

`main.ipynb` 把同样的流程拆成可单步执行的单元，适合边看效果边调：

| 单元 | 作用 |
|---|---|
| 获取选择题 / 分析题 / 画图题 / 计算题 | 截图（每个单元跑之前先滑到对应题型开头） |
| 提取文字（OCR） | `TextExtraction.save()` |
| 生成 Word | `WordBuilder.save()` |
| 检查产物 | 打印各题型的图片 / txt / Word 数量 |

### 典型一次运行

**整卷（一份卷子混着好几类题型）**

1. 模拟器打开试卷预览，滑到**最上面**；
2. `python main.py` → 选 `1`（一条龙）；
3. 卷名回车（比如 `期中卷`）、题量填 `200`、回车开始；
4. 跑完自动接着做文字、Word 和统计，直接看最后打印的核对结果即可。

**分题型**

1. 滑到「选择题」开头；
2. `python main.py` → 选 `3`（单题型）→ 选 `1`（选择题）→ 题量 → 回车开始；
3. 采完会问「继续提取文字并导出 Word？」，按 `y` 就一路做完；
4. 换下一个题型重复第 1~2 步（或者一开始就选「全部依次」）。

---

## 输出说明

```
resources/
├── row_pngs/                 ① 题目截图（每张一道题，宽 1600）
│   ├── 选择题/273.png
│   ├── 分析题/1.png
│   └── …
├── row_paper/                ① 混合试卷（截图 + 文字 + Word）
│   └── 期中卷/
│       ├── pngs/                 图片都放这个子目录
│       │   ├── 1.png                 顺序号，不是题号
│       │   ├── 2.png
│       │   └── …
│       └── txts/                 ② 对应的文字，文件名与图片顺序号一致
│           ├── 1.txt
│           ├── 1_formula.txt
│           └── …
├── row_txt/                  ② 识别出的文字
│   ├── 选择题/273.txt             纯文字
│   ├── 选择题/275_formula.txt     含公式（公式片段用 $...$ 标出）
│   ├── 选择题/436_table.txt       含表格
│   ├── 选择题/481_image.txt       含图像（图形）
│   └── …
└── word_output/              ③ 题库文档
    ├── 选择题题库.docx            按题型
    ├── 期中卷.docx               混合试卷（文件名就是卷名）
    └── …
```

- `row_paper/<卷名>/pngs` 里是**整卷**的截图，文件名是保存顺序（`1.png` 是这一卷的第一道题），
  不是题目编号——因为整卷里每类题型的题号都从 1 开始，用题号会重名；
- 图片、文字分放在 `pngs` / `txts` 两个子目录，文件名一一对应（`3.png` ↔ `3_formula.txt`），
  后面再加别的产物（比如答案、解析）也能各占一个子目录；
- 混合卷导出的 Word 叫 `<卷名>.docx`，每道题前面写「第N题」（N 是顺序号）；

- 文件名就是**试卷里的题目编号**（题目 273 → `273.png` / `273.txt` / Word 里的「第273题」），三个目录一一对应；
- 编号不连续就说明中间有题没截到，日志里会有 `编号从 N 直接跳到 M` 的提示；
- 带 `_formula` / `_table` / `_image` 后缀的题，在 Word 里是**题目原图**（等比缩放铺满正文宽度），因为公式、表格、图形转成文字都会丢内容；
- 不带后缀的纯文字题是**可编辑文字**，每个选项单独一段；
- `row_txt` 里带后缀的题，就是需要重点核对的那批（菜单 6) 检查产物 会分别统计三类数量）。

单题 txt 的样子：

```
某商品市场需求曲线为$D=10-P$，供给曲线为$S=2+P$。如果政府设置价格上限为3，那么会导致( )

A 市场过剩

B 市场短缺

C 都有可能

D 都不会
```

---

## 配置说明

所有可调项都在 [`src/common/const.py`](src/common/const.py)，常用的几个：

| 常量 | 默认值 | 说明 |
|---|---|---|
| `EMULATOR_WIDTH` / `EMULATOR_HEIGHT` | `1600` / `900` | 模拟器画面分辨率，换了分辨率要改 |
| `ADB_PATH` | `None` | 留空自动找；找不到 adb 时填绝对路径 |
| `ADB_SERIAL` | `None` | 多开时填 `adb devices` 里的序列号 |
| `ADB_DURATION` | `1500` | 一次滑动的时长（毫秒）。太短会触发惯性甩屏 |
| `CARD_TOP_MARGIN` / `CARD_BOTTOM_MARGIN` | `30` / `52` | 裁图时题干上方、选项下方的留白（虚拟机像素） |
| `CARD_SAFE_TOP` | `130` | 画面顶部被 App 标题栏挡住的高度 |
| `TARGET_HEADER_TOP` | `220` | 翻页后希望下一题标题行停在的位置 |
| `SAME_RATIO` | `0.008` | 兜底去重阈值：只有「题目N」读不出来时才用指纹比较 |
| `PNG_TYPES` | 选择题/分析题/画图题/计算题 | 菜单里列出的题型，按自己的试卷改 |
| `DEFAULT_PAGES` | `10` | 每次采集的默认题量上限（回车即用，可手动输入） |
| `PAPER_FOLDER` | `row_paper` | 混合试卷的输出目录名（`resources/row_paper/<卷名>/pngs/`） |
| `PAPER_PNGS` | `pngs` | 卷子目录下放图片的子目录名 |
| `PAPER_TXTS` | `txts` | 卷子目录下放文字的子目录名 |
| `PAPER_TYPES` | 单选/多选/判断/填空/分析/计算/画图… | 页脚里可能出现的题型名，混合卷靠它区分分区 |
| `PAPER_FOOTER_WIDTH` / `PAPER_FOOTER_PAD` / `PAPER_FOOTER_HEIGHT` | `620` / `6` / `26` | 读页脚题型时裁多大一条 |
| `PAPER_TYPE_CHECK_EVERY` | `5` | 每存几题复核一次页脚题型（整卷题号连续时靠它换标签） |
| `PAPER_JUMP` | `4` | 题号比上一题大这么多以上就按「没读出来」处理 |
| `PAPER_RECENT` | `5` | 题号读不出时，和最近几张比指纹兜底 |
| `TESSERACT_PATH` | 本机 Tesseract 路径 | OCR 可执行文件路径 |
| `TESSERACT_LANG` / `TESSERACT_CONFIG` | `chi_sim+eng` / `--psm 6` | OCR 语言与版面模式 |
| `OCR_FORMULA_SUFFIX` / `OCR_TABLE_SUFFIX` / `OCR_IMAGE_SUFFIX` | `_formula` / `_table` / `_image` | 三类题在 txt 文件名上的后缀 |
| `SHAPE_TABLE_H_LINES` / `SHAPE_TABLE_V_LINES` | `3` / `3` | 至少几条长横线 + 长竖线才判为表格 |
| `SHAPE_TABLE_H_RATIO` / `SHAPE_TABLE_V_RATIO` | `0.18` / `0.12` | 横线占画面宽、竖线占画面高的最低比例 |
| `SHAPE_FIGURE_SPAN` | `100` | 连续多少行都有墨迹就判为图像 |
| `SHAPE_LINE_GAP` | `3` | 找长直线前补齐几像素的缝（表格格子之间有缝） |
| `WORD_FONT` / `WORD_FONT_SIZE` | `宋体` / `10.5` | Word 正文字体与字号 |
| `WORD_TITLE_SUFFIX` | `题库` | 输出的 Word 文件名后缀 |
| `WORD_QUESTION_TITLE` | `第%d题` | 每题前面的小标题格式 |
| `VERBOSE` | `True` | 是否打印滑动、通道等过程信息 |

---

## 常见问题

**Q：截图位置不对、漏题、切到半道题？**
先在主菜单选 `7) 调试`——截一张整屏，打印题卡位置和读出来的题目编号。常见原因：

- 画面顶部标题栏更高/更矮 → 调 `CARD_SAFE_TOP`；
- 翻页后题目位置偏移 → 调 `TARGET_HEADER_TOP`；
- 留白不合心意 → 调 `CARD_TOP_MARGIN` / `CARD_BOTTOM_MARGIN`。

**Q：混合试卷（`row_paper`）的文件名为什么是 1、2、3，而不是题号？**
因为整卷里每类题型的题号都从 1 开始（`题目1` 会出现好几次），拿题号当文件名会互相覆盖。
所以混合卷用**保存顺序**当文件名，去重则用「(题型, 题号)」这个组合——题型是从页脚
（`… | 单选题 | 易`）读出来的。日志里每条都写着 `已保存 期中卷\8.png（分析题 题目1，…）`，
对着看就知道每张图是哪道题。

**Q：混合卷跑到某个题型开头，日志里没有「题型切换」？**
只有在**题号往回走**时才去读页脚确认题型。如果这份卷子的题号是整卷连续、不按题型重置的，
就没有"回退"这个信号，题型标签会靠每存 5 题复核一次来纠正，可能滞后几道；
这不影响图的完整性和数量，只影响日志和结尾统计里的题型名字。

**Q：文件名为什么不是从 1 开始，而是 273 这种？**
文件名就是试卷里的**题目编号**。这样跳过的题、换题型的题都不会让后面的编号错位，
`row_pngs` / `row_txt` / Word 三处也能一一对应。如果发现编号不连续，说明中间有题没截到，
日志里会有 `编号从 N 直接跳到 M` 的提示。

**Q：txt 文件名上的 `_formula` / `_table` / `_image` 是什么意思？**
这是这道题的内容特征，用来把"OCR 靠不住、需要对着原图核对"的题挑出来：

- `_formula`：文字里有公式（斜体变量、上下标容易被认错）；
- `_table`：版面上有表格（成组的贯穿长横线 + 长竖线），OCR 出来会变成一串错位的数字；
- `_image`：版面上有插图（曲线、示意图），OCR 完全认不出图形；

带后缀的题在 Word 里会直接贴原图，纯文字题才转成可编辑文字。
标签是按版面自动判断的，偶尔会有个别误判——**看图核对时以图片为准**。

**Q：日志里出现「第N题一屏放不下，已跳过」？**
这道题比一屏还高（正文超过约 620px），程序不会硬截成两张，而是跳过并在结束时列出题号，
需要你手动补截。想改这个行为可以看 `GetScreenshot.save()` 里 `TALL_RATIO` 那一段。

**Q：跑到一半提示「连续 3 帧画面没有变化，判定已经到底」？**
滑动可能被吞掉了（虚拟机卡顿、窗口失焦等）。程序会先重试一次再判定，如果确实还有题，
多半是模拟器页面不在试卷列表上；点一下模拟器画面再跑一次即可。

**Q：提示「没找到 adb，改用鼠标截图 + 拖拽」？**
把 `const.ADB_PATH` 填成模拟器自带 `adb.exe` 的绝对路径（MuMu 在 `…\MuMuPlayer\nx_device\15.0\shell\adb.exe`）。鼠标兜底能跑，但要求窗口不被遮挡、位置准确。

**Q：虚拟机重启后截图失败，`adb devices` 是空的？**

这是最常见的问题。MuMu 12 的 adb 走 TCP（默认端口 **16384**），虚拟机重启后 adb server 里那条旧连接
失效了，但 `MuMuNxDevice` 和 adb server 进程都还在——于是 `adb devices` 为空，脚本调
`adb exec-out screencap` 就报 `no devices/emulators found` 或 `device offline`。

手动连一下即可（用 MuMu 自带的 adb，就是 `ADB_CANDIDATES` 里那个路径）：

```powershell
# 进到 MuMu 自带 adb 所在目录（版本号随安装而定）
cd "…\MuMuPlayer\nx_device\15.0\shell"

.\adb.exe connect 127.0.0.1:16384
.\adb.exe devices
#   List of devices attached
#   127.0.0.1:16384    device
```

连接不上或显示 `offline` 时，重启 adb 服务再连（仍在上面那个目录里）：

```powershell
.\adb.exe kill-server
.\adb.exe start-server
.\adb.exe connect 127.0.0.1:16384
```

别的补充：

- **多开**：端口按实例递增，第一台 `16384`、第二台 `16416`、第三台 `16448`…（MuMu 多开器里能看到）；
- **报 `adb server version doesn't match`**：说明有别的 adb 抢了 5037 端口，先 `taskkill /IM adb.exe /F`，再只用 MuMu 自带的 adb；
- **验证截图链路**：`adb shell screencap -p /sdcard/t.png` 再 `adb pull /sdcard/t.png .`，能拉出 1600×900 的图就正常；
  注意别用 PowerShell 的 `>` 重定向保存 PNG，会把二进制写坏；
- **想免掉这步手动操作**：脚本启动时会自己跑一次 `adb devices`——只有一个设备就用它，
  有多个就优先挑 `127.0.0.1:xxxx` 那条（模拟器的 adb 通道），日志里会打印
  `[提示] adb 检测到 2 个设备，使用 127.0.0.1:16384`。想锁死某一台就在 `const.py` 里填
  `ADB_SERIAL`；设备列表为空时仍需要手动 `adb connect`（见上）。

**Q：滑动后页面飞出去很远 / 滑不动？**
- 飞出去：`ADB_DURATION` 加大（比如 2000），松手太快会被识别成「甩」；
- 滑不动：可能已经到试卷末尾，或页面不在试卷列表上。

**Q：Tesseract 报错 / 中文乱码？**
确认 `TESSERACT_PATH` 正确，并且安装时勾了 `chi_sim`：`tesseract --list-langs` 应该能看到 `chi_sim`。

**Q：公式识别不准？**
当前方案的已知短板：截图里的公式是斜体，`Q_d` 常被认成 `O,`、`P` 常被认成 `尸`。脚本的处理方式是：

1. 把公式片段用 `$...$` 标出来；
2. 含公式的题在 txt 上标 `_formula`，Word 里直接用原图；
3. 跑完打印「建议核对」的列表。

要真正还原公式，需要把 OCR 换成多模态模型（Qwen-VL / GPT-4o / Mathpix 等）输出 LaTeX，改动点只有 `TextExtraction.write()` 里调用引擎的那一行。

**Q：Word 里公式不能编辑？**
是的，公式题是图片。等接入 LaTeX 后可以改成 OMML 公式对象（pandoc 或 `latex2mathml` 转换）。

**Q：有超长的题被跳过了？**
比一屏还高的题当前会打印提示并跳过（`[提示] … 一屏放不下`），需要人工补截，或后续实现分屏拼接。

**Q：`pip install` 报 `check_hostname requires server_hostname`？**
旧版 pip（21.x）走 HTTPS 源时可能报这个，换成 HTTP 源即可：

```bash
.venv\Scripts\python.exe -m pip install -r reqiurements.txt ^
    --index-url http://pypi.tuna.tsinghua.edu.cn/simple ^
    --trusted-host pypi.tuna.tsinghua.edu.cn
```

---

## 开发者指南

### 目录结构

```
Sciyardcampus_file_export/
├── main.py                        # 交互式菜单入口（只有 start()）
├── main.ipynb                     # 同样流程的 Notebook 版本
├── reqiurements.txt               # 依赖
├── resources/                     # 产物（不进版本库）
│   ├── row_pngs/                  #   题目截图（按题型）
│   ├── row_paper/                 #   混合试卷截图（<卷名>/pngs/<顺序号>.png）
│   ├── row_txt/                   #   识别文字
│   └── word_output/               #   题库 Word
├── src/
│   ├── common/
│   │   ├── const.py               # 所有常量与可调参数
│   │   ├── figuresio.py           # 图片路径（resources/row_pngs）
│   │   └── filesio.py             # 文本 / Word 路径（row_txt、word_output）
│   └── modules/
│       ├── tools/
│       │   ├── emulator_screen.py # 虚拟机窗口 / 屏幕坐标适配（鼠标兜底用）
│       │   ├── android_device.py  # adb 截图与滑动、鼠标拖拽兜底
│       │   ├── question_card.py   # 题卡识别、裁剪、去重指纹、读题目编号
│       │   ├── question_shape.py  # 判断题卡里有没有表格 / 图像
│       │   └── ocr.py             # Tesseract 薄封装（读正文、读标题行编号）
│       ├── datapreparation/
│       │   ├── screenshot.py      # GetScreenshot：按题型截图流水线
│       │   ├── paper_screenshot.py # GetPaperScreenshot：混合试卷截图流水线
│       │   ├── text_extraction.py # TextExtraction：OCR 流水线
│       │   └── paper_text_extraction.py # PaperTextExtraction：混合试卷 OCR
│       ├── process/
│       │   ├── word_builder.py    # WordBuilder：生成题库 Word
│       │   └── paper_word_builder.py # PaperWordBuilder：混合试卷 Word
│       └── interactions/          # 交互菜单（main.py 的实现都在这儿）
│           ├── console.py         #   Console：读数字 / 是否 / 选项，q 取消
│           ├── status.py          #   Status：菜单顶部状态、检查产物报表
│           ├── actions.py         #   Actions：采集 / 提取文字 / 导出 Word
│           └── menus.py           #   Menus：每个菜单项的问答流程与分发
└── test/
    ├── test_1.py … test_6.py      # 各模块的手工测试脚本
```

### 模块职责

| 模块 | 职责 | 关键方法 |
|---|---|---|
| `EmulatorScreen` | 虚拟机画面与屏幕坐标换算、窗口自动探测、DPI 感知 | `window_box()`、`scale()`、`to_screen()` |
| `AndroidDevice` | 截图与滑动：优先 adb，失败或无 adb 时退回鼠标 | `capture()`、`swipe()`、`adb_swipe()`、`drag()` |
| `Ocr` | Tesseract 薄封装，统一可执行文件路径 | `prepare()`、`text()` |
| `Card` / `QuestionCard` | 从整屏帧里认出每道题、裁剪、读编号、读页脚题型、生成去重指纹 | `split()`、`crop()`、`header_number()`、`footer_type()`、`fingerprint()` |
| `QuestionShape` | 判断题卡版面：有没有表格（长横线+长竖线）、有没有图像（连续有墨迹） | `kinds()`、`has_table()`、`has_figure()` |
| `GetScreenshot` | 按题型截图：截屏 → 切题 → 按编号去重 → 存图 → 对齐翻页 | `save()`、`probe()`、`first_unsaved()`、`target_scroll()` |
| `GetPaperScreenshot` | 混合试卷截图：整卷一次滚到底，按 (分区, 题号) 去重、按顺序号存图 | `save()`、`probe()`、`first_unsaved()`、`repeated()` |
| `TextExtraction` | OCR 主流程：识别 → 分段 → 公式标记 → 特征打标签 → 写 txt | `save()`、`write()`、`mark_math()`、`kinds_of()` |
| `PaperTextExtraction` | 混合试卷的 OCR：`row_paper/<卷名>/pngs` → `txts`，文件名是顺序号 | `save()`、`write()` |
| `WordBuilder` | 按题型合成 Word：带标签的题贴图、纯文本题转段落 | `save()`、`build()`、`add_picture()` |
| `PaperWordBuilder` | 混合试卷合成 Word：`row_paper/<卷名>/txts` → `word_output/<卷名>.docx` | `save()`、`build()`、`indexes()` |
| `Console` | 终端输入原语：读数字 / 是否 / 选项，回车用默认值、q 取消 | `ask_int()`、`ask_yes()`、`choose()`、`pause()` |
| `Status` | 只读统计与展示：菜单顶部一屏、检查产物报表 | `banner()`、`report()`、`count_pngs()` |
| `Actions` | 菜单选中后真正干活：采集 / 提取文字 / 导出 Word | `capture()`、`capture_paper()`、`extract_text()`、`build_word()` |
| `Menus` | 菜单项清单、每一项的问答流程、按键分发 | `show()`、`run()`、`paper()`、`single_type()` |

### 数据流

```
AndroidDevice.capture()  ──► PIL.Image（1600×900 帧）
        │
QuestionCard.split()     ──► [Card(header_top, top, bottom, footer), …]
        │
QuestionCard.header_number() ──► 题目编号（去重、命名的唯一键）
        │
QuestionCard.crop()      ──► 题卡图 ──► resources/row_pngs/<题型>/<题号>.png
        │                                  或 resources/row_paper/<卷名>/pngs/<顺序号>.png
        │
TextExtraction.write()   ──► resources/row_txt/<题型>/<题号>[_formula|_table|_image].txt
        │
WordBuilder.build()      ──► resources/word_output/<题型>题库.docx
```

混合试卷那条路的文字提取只是换了目录、文件名改成顺序号：

```
row_paper/<卷名>/pngs/<顺序号>.png
        │  PaperTextExtraction.write()（复用 TextExtraction 的分段/公式/版面判断）
        ▼
row_paper/<卷名>/txts/<顺序号>[_formula|_table|_image].txt
        │  PaperWordBuilder.build()（页面/标题/贴图复用 WordBuilder）
        ▼
resources/word_output/<卷名>.docx
```

混合试卷那条路的去重键是 `(分区, 题号)`：

```
QuestionCard.header_number()  ──► 题号（同一分区内递增）
QuestionCard.footer_type()    ──► 题型名（"… | 单选题 | 易" 的中间那段）
        │
题号回退 → 读页脚确认题型 → 分区 +1 → 新分区里题号重新从 1 数
```

### 扩展点

- **换 OCR 引擎**：`TextExtraction.write()` 里只有一处 `pytesseract.image_to_string(...)`，替换成自己的 `ocr(image) -> str` 即可；如果新引擎直接吐 LaTeX（Mathpix / 多模态模型），记得跳过 `mark_math()`，否则 `$...$` 会被重复包裹。
- **加题型**：截图时传新的 `png_type`（会自动建目录），再跑 OCR 和 Word；记得把新题型加进 [`const.py`](src/common/const.py) 的 `PNG_TYPES`，菜单里才会出现。
- **改 Word 版式**：`WordBuilder.setup()` 管页面/字体，`add_title()` / `add_text()` / `add_picture()` 管每题内容。
- **适配别的 App 版式**：识别锚点集中在 `QuestionCard`（红字标题 `CARD_RED`、正文亮度 `CARD_DARK_LUM`、页脚亮度 `CARD_FOOTER_LUM` 与最小高度 `CARD_FOOTER_MIN`、顶部遮挡 `CARD_SAFE_TOP`）。
- **调试单个环节**：`GetScreenshot.probe()` 看切题；`QuestionCard.split(frame)` 可以单独喂任意截图。

### 测试脚本

| 脚本 | 内容 |
|---|---|
| `test/test_1.py` | 路径工具（`FilesIO` / `FiguresIO`） |
| `test/test_2.py` | 最初的固定区域截图（历史版本） |
| `test/test_3.py` | 截图主流程 |
| `test/test_4.py` | OCR 主流程 |
| `test/test_5.py` | Word 生成 |

> `resources/` 不进版本库，测试前需要有对应产物，或者先跑一遍截图。

---

## 已知限制

1. **公式 OCR 不保证准确**：斜体变量、上下标容易认错，所以含公式的题在 Word 中以图片呈现，并在 txt 文件名上标注 `_formula`；
2. **依赖这套页面版式**：需要「题目N（x分）」红色标题行 + 浅灰「单选题 | 易 … 共享试题」页脚；
3. **比一屏还高的题会被跳过**：正文超过约 620px 的题截不成一张完整图，程序会跳过并在结束时列出题号，需要手动补截；
4. **题目编号依赖标题行 OCR**：编号读不出来时会用「上一题编号 + 1」暂存并打警告，编号不连续时日志里会提示跳号；
5. **只支持 Windows**：用到了 Win32 的 DPI 感知、窗口客户区接口；
6. **题型切换需要手动**：截图只会往下走，每个题型开始前需要把试卷滑到该题型开头（混合试卷那条路不用）；
7. **混合试卷的 Word 是按顺序号排的**：文档里写「第1题、第2题…」，对应 `pngs/1.png`，
   不是试卷页面上印的题号（那个题号在整卷里会重复）；
8. **混合卷的文件名是顺序号**：重跑会从 `1.png` 覆盖，中间新增或删减会让后面的序号整体错位；
   开跑前程序会问要不要先清空该卷的旧图，或者换个卷名；
9. **菜单是交互式的**：不再支持命令行参数，需要脚本化调用的话直接 import 对应类（见「快速开始」里的 py 示例）。

## 许可证

[MIT License](LICENSE) © 2026 御河DE天街

仓库：<https://github.com/FantasySilence/Sciyardcampus_file_export>
