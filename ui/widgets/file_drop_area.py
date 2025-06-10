import os
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QLabel
from PyQt5.QtGui import QDragEnterEvent, QDropEvent
from utils.general import Path


TIP_TEXT = "拖拽文件到此处"


class FileDropArea(QLabel):
    """文件拖放区"""
    add_file_signal = pyqtSignal(str) # 添加文件信号

    def __init__(self) -> None:
        super().__init__(TIP_TEXT)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet(self.get_stylesheet())
        self.setAcceptDrops(True)
        self.setMinimumHeight(100)

    @staticmethod
    def get_stylesheet() -> str:
        return """border: 2px dashed #aaa; border-radius: 10px; padding: 20px;
            background-color: #f9f9f9; font-size: 16px;"""

    def dragEnterEvent(self, a0: QDragEnterEvent | None) -> None:
        """处理拖拽进入事件"""
        if a0 is None:
            return
        event = a0

        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, a0: QDropEvent | None) -> None:
        """处理拖拽事件"""
        if a0 is None:
            return
        event = a0

        data = event.mimeData()
        for url in data.urls():
            file_path = url.toLocalFile()
            if os.path.isfile(file_path):
                self.add_file(file_path)
        event.acceptProposedAction()
    
    def add_file(self, file_path: Path) -> None:
        """添加文件"""
        # 发出信号，等待处理
        self.add_file_signal.emit(file_path)
