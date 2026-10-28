# ================================================================== #
# @Author: Fantasy_Silence                                           #
# @Time: 2026-10-29                                                  #
# @IDE: Visual Studio Code & PyCharm                                 #
# @Python: 3.9.7                                                     #
# ================================================================== #
# @Description: Tesseract 的薄封装，统一可执行文件路径                  #
# ================================================================== #
import os
import shutil
from typing import Optional

import pytesseract
from PIL import Image

from src.common import const


class Ocr:

    """
    Tesseract 的一个薄封装

    读题目文字、读标题行的"题目N"都走这里，省得每处都去设置 tesseract_cmd
    """

    _prepared = False

    @staticmethod
    def prepare():

        """
        找到 tesseract.exe：先看 const 里写的路径，再退回 PATH
        """

        if Ocr._prepared:
            return

        path = const.TESSERACT_PATH if os.path.exists(const.TESSERACT_PATH) else shutil.which("tesseract")
        if path is None:
            raise RuntimeError(
                "没找到 Tesseract，请先安装（含 chi_sim 语言包），"
                "再把 const.TESSERACT_PATH 指到 tesseract.exe"
            )

        pytesseract.pytesseract.tesseract_cmd = path
        Ocr._prepared = True

    @staticmethod
    def text(image: Image.Image, lang: Optional[str] = None, config: Optional[str] = None) -> str:

        """
        image: 要识别的图（整张题卡或某个局部）
        lang / config: 不传就用 const 里的默认值
        """

        Ocr.prepare()
        return pytesseract.image_to_string(
            image,
            lang=lang or const.TESSERACT_LANG,
            config=config or const.TESSERACT_CONFIG,
        )
