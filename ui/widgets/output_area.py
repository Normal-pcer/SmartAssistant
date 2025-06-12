from PyQt5.QtWidgets import QTextEdit
from PyQt5.QtGui import QTextCursor
from utils.general import log

class OutputArea(QTextEdit):
    """输出区域"""

    def __init__(self) -> None:
        super().__init__()
        self.setReadOnly(True)
        self.setStyleSheet("background-color: #f0f0f0;")
    
    def append_text(self, text: str) -> None:
        """
        在输出区域末尾追加文本并刷新显示，不会自动换行
        """
        log.debug(f"OutputArea::append_text: {text}")
        self.moveCursor(QTextCursor.End)
        self.insertPlainText(text)
        self.update()
