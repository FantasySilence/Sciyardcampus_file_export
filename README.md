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
| Python | 3.9（开发时用的 `.venv`，克隆后需自行创建） |
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

自检（截一张整屏，打印识别到的题卡位置，不改动任何数据）：

```bash
python main.py probe
```

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

### 方式一：命令行（`main.py`）

```bash
python main.py                  # 全套：截图 -> OCR -> Word -> 核对
python main.py capture          # 只截图（会提示你把试卷滑到每个题型的开头）
python main.py capture -t 选择题 # 只截某一种题型
python main.py ocr              # 只做文字提取
python main.py word             # 只生成 Word
python main.py check            # 只打印产物统计
python main.py probe            # 调试：截整屏、打印题卡位置和题目编号
```

`capture` 会在每个题型开始前停下等回车（脚本只会往下截）：

```
把模拟器里的试卷滑到「选择题」开头，回车开始截图：
```

题型列表与顺序写在 `main.py` 顶部的 `PNG_TYPES` 里，按自己的试卷改即可。

> `pages` 是题量上限（默认 10）。试卷题量很大时记得给够，例如
> `python main.py capture -p 600`；不够会在截到上限时停下，日志里会提示 `已达到 pages=N`。

> 截图过程会实时打印「已保存 选择题\273.png」「编号从 273 直接跳到 275，中间可能有题没截到」
> 这类信息，跑完还会汇总保存数量和跳过的题号，方便对照检查。

### 方式二：Notebook（`main.ipynb`）

`main.ipynb` 把同样的流程拆成可单步执行的单元，适合边看效果边调：

| 单元 | 作用 |
|---|---|
| 获取选择题 / 分析题 / 画图题 / 计算题 | 截图（每个单元跑之前先滑到对应题型开头） |
| 提取文字（OCR） | `TextExtraction.save()` |
| 生成 Word | `WordBuilder.save()` |
| 检查产物 | 打印各题型的图片 / txt / Word 数量 |

### 典型一次运行

1. 模拟器打开试卷预览，滑到「选择题」开头；
2. `python main.py capture`，按提示逐个题型回车；
3. `python main.py ocr`，跑完看提示里「含公式、建议核对」的列表；
4. `python main.py word`；
5. `python main.py check` 核对数量，然后打开 `resources/word_output/` 里的 docx。

---

## 输出说明

```
resources/
├── row_pngs/                 ① 题目截图（每张一道题，宽 1600）
│   ├── 选择题/273.png
│   ├── 分析题/1.png
│   └── …
├── row_txt/                  ② 识别出的文字
│   ├── 选择题/273.txt             纯文字
│   ├── 选择题/275_formula.txt     含公式（公式片段用 $...$ 标出）
│   ├── 选择题/436_table.txt       含表格
│   ├── 选择题/481_image.txt       含图像（图形）
│   └── …
└── word_output/              ③ 题库文档
    ├── 选择题题库.docx
    ├── 分析题题库.docx
    └── …
```

- 文件名就是**试卷里的题目编号**（题目 273 → `273.png` / `273.txt` / Word 里的「第273题」），三个目录一一对应；
- 编号不连续就说明中间有题没截到，日志里会有 `编号从 N 直接跳到 M` 的提示；
- 带 `_formula` / `_table` / `_image` 后缀的题，在 Word 里是**题目原图**（等比缩放铺满正文宽度），因为公式、表格、图形转成文字都会丢内容；
- 不带后缀的纯文字题是**可编辑文字**，每个选项单独一段；
- `row_txt` 里带后缀的题，就是需要重点核对的那批（`main.py check` 会分别统计三类数量）。

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
先跑 `python main.py probe` 看整屏、题卡位置和读出来的题目编号。常见原因：

- 画面顶部标题栏更高/更矮 → 调 `CARD_SAFE_TOP`；
- 翻页后题目位置偏移 → 调 `TARGET_HEADER_TOP`；
- 留白不合心意 → 调 `CARD_TOP_MARGIN` / `CARD_BOTTOM_MARGIN`。

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
- **想免掉这步手动操作**：在 `const.py` 里把 `ADB_SERIAL = "127.0.0.1:16384"` 固定下来（多开时锁定某一台），
  或者在 `AndroidDevice.adb()` 里加一次「设备为空就自动 connect」的逻辑。

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
├── main.py                        # 命令行入口（截图 / OCR / Word / 核对）
├── main.ipynb                     # 同样流程的 Notebook 版本
├── reqiurements.txt               # 依赖
├── resources/                     # 产物（不进版本库）
│   ├── row_pngs/                  #   题目截图
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
│       │   ├── screenshot.py      # GetScreenshot：截图流水线
│       │   └── text_extraction.py # TextExtraction：OCR 流水线
│       └── process/
│           └── word_builder.py    # WordBuilder：生成题库 Word
└── test/
    ├── test_1.py … test_5.py      # 各模块的手工测试脚本
```

### 模块职责

| 模块 | 职责 | 关键方法 |
|---|---|---|
| `EmulatorScreen` | 虚拟机画面与屏幕坐标换算、窗口自动探测、DPI 感知 | `window_box()`、`scale()`、`to_screen()` |
| `AndroidDevice` | 截图与滑动：优先 adb，失败或无 adb 时退回鼠标 | `capture()`、`swipe()`、`adb_swipe()`、`drag()` |
| `Ocr` | Tesseract 薄封装，统一可执行文件路径 | `prepare()`、`text()` |
| `Card` / `QuestionCard` | 从整屏帧里认出每道题、裁剪、读编号、生成去重指纹 | `split()`、`crop()`、`header_number()`、`fingerprint()` |
| `QuestionShape` | 判断题卡版面：有没有表格（长横线+长竖线）、有没有图像（连续有墨迹） | `kinds()`、`has_table()`、`has_figure()` |
| `GetScreenshot` | 截图主流程：截屏 → 切题 → 按编号去重 → 存图 → 对齐翻页 | `save()`、`probe()`、`first_unsaved()`、`target_scroll()` |
| `TextExtraction` | OCR 主流程：识别 → 分段 → 公式标记 → 特征打标签 → 写 txt | `save()`、`write()`、`mark_math()`、`kinds_of()` |
| `WordBuilder` | 按题型合成 Word：带标签的题贴图、纯文本题转段落 | `save()`、`build()`、`add_picture()` |

### 数据流

```
AndroidDevice.capture()  ──► PIL.Image（1600×900 帧）
        │
QuestionCard.split()     ──► [Card(header_top, top, bottom, footer), …]
        │
QuestionCard.header_number() ──► 题目编号（去重、命名的唯一键）
        │
QuestionCard.crop()      ──► 题卡图 ──► resources/row_pngs/<题型>/<题号>.png
        │
TextExtraction.write()   ──► resources/row_txt/<题型>/<题号>[_formula|_table|_image].txt
        │
WordBuilder.build()      ──► resources/word_output/<题型>题库.docx
```

### 扩展点

- **换 OCR 引擎**：`TextExtraction.write()` 里只有一处 `pytesseract.image_to_string(...)`，替换成自己的 `ocr(image) -> str` 即可；如果新引擎直接吐 LaTeX（Mathpix / 多模态模型），记得跳过 `mark_math()`，否则 `$...$` 会被重复包裹。
- **加题型**：截图时传新的 `png_type`（会自动建目录），再跑 OCR 和 Word；`main.py` 里记得加进 `PNG_TYPES`。
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
6. **题型切换需要手动**：截图只会往下走，每个题型开始前需要把试卷滑到该题型开头。

## 许可证

[MIT License](LICENSE) © 2026 御河DE天街

仓库：<https://github.com/FantasySilence/Sciyardcampus_file_export>
