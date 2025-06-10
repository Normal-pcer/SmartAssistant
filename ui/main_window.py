"""
UI 主窗口
"""

from typing import Optional

from PyQt5.QtWidgets import QMainWindow

from core.assistant import Assistant
from utils.general import *

class MainWindow(QMainWindow):
    """
    程序的主窗口
    """
    assistant: Assistant # 所有实际逻辑的处理器

    def __init__(self, assis: Optional[Assistant] = None):
        """
        assis: 传入指定的逻辑处理器
        """
        assis = set_default(assis, Assistant())

        pass