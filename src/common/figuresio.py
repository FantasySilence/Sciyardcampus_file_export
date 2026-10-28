# ================================================================== #
# @Author: Fantasy_Silence                                           #
# @Time: 2026-10-28                                                  #
# @IDE: Visual Studio Code & PyCharm                                 #
# @Python: 3.9.7                                                     #
# ================================================================== #
# @Description: 这是一个图片IO流类，用于图片读取与保存                  #
# ================================================================== #
import os
from typing import Optional


class FiguresIO:

    """
    图片IO流，便于图片读取或保存
    """

    @staticmethod
    def loadFigure(fig_name: Optional[str] = None, sub_dir: Optional[str] = None) -> str:

        """
        fig_name: 图片名称
        sub_dir: 子文件夹（比如"单选题"），路径变成 resources/row_pngs/单选题/xxx.png
        """

        # ------ common路径 ------ #
        common_path = os.path.dirname(os.path.abspath(__file__))

        # ------ src路径 ------ #
        src_path = os.path.dirname(common_path)
        ROOTPATH = os.path.dirname(src_path)

        # ------ 输出目录：resources/row_pngs[/子文件夹] ------ #
        folder = ROOTPATH + "/resources/row_pngs"
        if sub_dir is not None:
            folder = folder + "/" + sub_dir

        # ------ 检查是否存在数据文件夹，不存在就创建一个 ------ #
        if not os.path.exists(folder):
            os.makedirs(folder)

        # ------ 输出图片路径 ------ #
        if fig_name == None:
            return folder
        else:
            return folder + "/" + fig_name
