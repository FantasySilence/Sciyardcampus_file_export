# =========================================================== #
# @Author: Fantasy_Silence                                    #
# @Time: 2026-10-28                                           #
# @IDE: Visual Studio Code & PyCharm                          #
# @Python: 3.9.7                                              #
# =========================================================== #
# @Description: 这是一个文件IO流类，用于文件读取与保存           #
# =========================================================== #
import os
from typing import Optional


class FilesIO:

    """
    文件IO流，便于文件读取或保存时自动获取文件路径
    """

    
    @staticmethod
    def loadText(filename: Optional[str] = None, sub_dir: Optional[str] = None) -> str:

        """
        filename: 文件名
        sub_dir: 子文件夹（比如"单选题"），路径变成 resources/row_txt/单选题/1.txt
        """

        # ------ common路径 ------ #
        common_path = os.path.dirname(os.path.abspath(__file__))

        # ------ src路径 ------ #
        src_path = os.path.dirname(common_path)
        ROOTPATH = os.path.dirname(src_path)

        # ------ 输出目录：resources/row_txt[/子文件夹] ------ #
        folder = ROOTPATH + "/resources/row_txt"
        if sub_dir is not None:
            folder = folder + "/" + sub_dir

        # ------ 检查是否存在数据文件夹，不存在就创建一个 ------ #
        if not os.path.exists(folder):
            os.makedirs(folder)

        # ------ 获取文件路径 ------ #
        if filename == None:
            return folder
        else:
            return folder + "/" + filename

    @staticmethod
    def loadWord(filename: Optional[str] = None) -> str:

        """
        filename: 文件名，路径是 resources/word_output/文件名
        """

        # ------ common路径 ------ #
        common_path = os.path.dirname(os.path.abspath(__file__))

        # ------ src路径 ------ #
        src_path = os.path.dirname(common_path)
        ROOTPATH = os.path.dirname(src_path)

        # ------ 输出目录：resources/word_output ------ #
        folder = ROOTPATH + "/resources/word_output"

        # ------ 检查是否存在数据文件夹，不存在就创建一个 ------ #
        if not os.path.exists(folder):
            os.makedirs(folder)

        # ------ 获取文件路径 ------ #
        if filename == None:
            return folder
        else:
            return folder + "/" + filename
    