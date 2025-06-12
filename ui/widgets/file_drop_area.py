import os
from typing import List, Optional
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import QListWidget, QMenu, QAbstractItemView
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QDragMoveEvent, QKeyEvent, QContextMenuEvent
from utils.general import Path


class FileDropArea(QListWidget):
    """支持文件拖放和删除、展示文件列表"""
    add_file_signal = pyqtSignal(Path)    # 添加文件信号（参数：文件路径）
    remove_file_signal = pyqtSignal(Path) # 删除文件信号（参数：文件路径）
    file_list: List[Path]

    def __init__(self) -> None:
        super().__init__()
        self.setAcceptDrops(True)
        self.setMinimumHeight(100)
        self.setMaximumHeight(150)
        self.file_list = []
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)  # 支持多选
        
        # 初始提示文本
        self.show_tip()

    def dragEnterEvent(self, e: Optional[QDragEnterEvent]) -> None:
        """处理拖拽进入事件"""
        if e is None:
            return
        if e.mimeData().hasUrls():
            e.acceptProposedAction()
    
    def dragMoveEvent(self, e: Optional[QDragMoveEvent]) -> None:
        """处理拖拽移动事件"""
        if e is None:
            return
        e.acceptProposedAction()

    def dropEvent(self, event: Optional[QDropEvent]) -> None:
        """释放鼠标，添加文件"""
        if event is None:
            return

        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if os.path.isfile(file_path):
                self.add_file(file_path)
        event.acceptProposedAction()

    def add_file(self, file_path: Path) -> None:
        """添加文件到列表"""
        if file_path in self.file_list:
            return
        
        # 如果是首次添加，清除提示项
        if not self.file_list:
            self.clear()
            self.file_list = []

        self.file_list.append(file_path)
        self.addItem(os.path.basename(file_path))

        # 发出添加信号
        self.add_file_signal.emit(file_path)

    def remove_file(self, file_path: Path) -> None:
        """从列表中删除文件"""
        if file_path in self.file_list:
            self.file_list.remove(file_path)
            self.remove_file_signal.emit(file_path)

    def keyPressEvent(self, e: Optional[QKeyEvent]) -> None:
        """键盘事件处理 - 支持 Delete 键删除"""
        if e is None:
            return
        super().keyPressEvent(e)

        # 处理删除键
        if e.key() in (Qt.Key_Delete, Qt.Key_Backspace):
            self.delete_selected_files()

    def contextMenuEvent(self, a0: Optional[QContextMenuEvent]) -> None:
        """右键菜单事件 - 创建删除菜单"""
        if a0 is None or not self.selectedItems():
            return
            
        event = a0

        # 创建上下文菜单
        menu = QMenu(self)
        delete_action = menu.addAction("删除选中文件")
        clear_action = menu.addAction("清空所有文件")
        
        # 显示菜单并获取选择
        action = menu.exec_(self.mapToGlobal(event.pos()))
        
        # 执行操作
        if action == delete_action:
            self.delete_selected_files()
        elif action == clear_action:
            self.clear_all_files()

    def delete_selected_files(self) -> None:
        """删除选中的文件项"""
        if not self.selectedItems():
            return
            
        # 倒序删除避免索引变动
        for item in reversed(self.selectedItems()):
            row = self.row(item)
            file_path = self.file_list[row]
            
            # 从列表中移除
            self.remove_file(file_path)
            self.takeItem(row)
        
        self.show_tip()

    def clear_all_files(self) -> None:
        """清空所有文件"""
        # 发出删除信号
        for file_path in self.file_list:
            self.remove_file_signal.emit(file_path)

        # 清空文件
        self.clear()
        self.file_list = []
    
    def show_tip(self) -> None:
        """如果文件列表为空，显示提示"""
        if self.file_list:
            return  # 存在文件
        self.addItem("拖拽文件到此处")
        if item := self.item(0):
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item.setFlags(Qt.ItemFlag.NoItemFlags)
