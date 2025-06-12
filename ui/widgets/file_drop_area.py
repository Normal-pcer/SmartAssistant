import os
from typing import List, Optional
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import  QListWidget
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QDragMoveEvent
from utils.general import Path


class FileDropArea(QListWidget):
    """文件拖放区"""
    add_file_signal = pyqtSignal(str)  # 添加文件信号
    file_list: List[Path]

    def __init__(self) -> None:
        super().__init__()
        self.setAcceptDrops(True)
        self.setMinimumHeight(100)
        self.setMaximumHeight(150)
        self.file_list = []

        self.addItem("拖拽文件到此处")
        if item := self.item(0):
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

    def dragEnterEvent(self, e: Optional[QDragEnterEvent]) -> None:
        """处理拖拽进入事件"""
        if e is None:
            return
        event = e
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dragMoveEvent(self, e: Optional[QDragMoveEvent]) -> None:
        """处理拖拽移动事件"""
        if e is None:
            return
        event = e
        event.acceptProposedAction()

    def dropEvent(self, event: Optional[QDropEvent]) -> None:
        """处理拖拽事件"""
        if event is None:
            return

        data = event.mimeData()
        for url in data.urls():
            file_path = url.toLocalFile()
            if os.path.isfile(file_path):
                self.add_file(file_path)
        event.acceptProposedAction()

    def add_file(self, file_path: Path) -> None:
        """添加文件"""
        if file_path in self.file_list:
            return
        
        if not self.file_list:
            self.clear()

        self.file_list.append(file_path)
        self.addItem(file_path)

        # 发出信号，等待其他处理
        self.add_file_signal.emit(file_path)

