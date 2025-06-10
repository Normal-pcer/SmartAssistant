from typing import List
from PyQt5.QtWidgets import QListWidget
from utils.general import Path


class FileInfo(QListWidget):
    """展示当前选择的文件信息"""

    file_list: List[Path]

    def __init__(self) -> None:
        super().__init__()
        self.file_list = []
        self.setMaximumHeight(100)
        self.setStyleSheet("font-size: 12px;")
    
    def add_file(self, file_path: Path) -> None:
        """添加文件"""
        if file_path in self.file_list:
            return

        self.addItem(file_path)
