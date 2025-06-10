"""
UI 主窗口
"""

from typing import Optional
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QTextEdit, QLabel
from PyQt5.QtGui import QIcon
from core.assistant import Assistant
from utils.general import set_default, Path, log
from utils.icon import get_icon
from ui.widgets.file_drop_area import FileDropArea
from ui.widgets.file_info import FileInfo
from ui.widgets.output_area import OutputArea

WINDOW_TITLE = "智能助手"
MIN_WINDOW_SIZE = (600, 500)
ICON_NAME = "assistant_icon"


class MainWindow(QMainWindow):
    """
    程序的主窗口
    """
    assistant: Assistant  # 所有实际逻辑的处理器
    always_on_top_flag: bool = True  # 当前是否置顶

    main_layout: QVBoxLayout
    main_widget: QWidget

    file_drop_area: FileDropArea
    file_info: FileInfo
    output_area: OutputArea

    def __init__(self, assis: Optional[Assistant] = None) -> None:
        """
        assis: 传入指定的逻辑处理器
        """
        assis = set_default(assis, Assistant())
        self.assistant = assis

        # 初始化窗体
        super().__init__()
        self.setWindowTitle(WINDOW_TITLE)
        self.setMinimumSize(*MIN_WINDOW_SIZE)
        self.setWindowIcon(QIcon(get_icon(ICON_NAME)))

        # 创建初始布局
        self.main_widget = QWidget()
        self.main_layout = QVBoxLayout(self.main_widget)
        self.setCentralWidget(self.main_widget)

        # 添加初始组件
        # 文件拖放区
        self.file_drop_area = FileDropArea()
        self.main_layout.addWidget(self.file_drop_area)

        # 文件展示区
        self.file_info = FileInfo()
        self.main_layout.addWidget(self.file_info)

        def on_add_file(file_path: Path):  # 添加文件时进行相关处理
            log.debug(f"on_add_file: {file_path}")
            self.assistant.selected_files.append(file_path)
            self.file_info.add_file(file_path)  # 刷新文件列表
        self.file_drop_area.add_file_signal.connect(on_add_file)

        # 命令输入区
        self.main_layout.addWidget(QLabel("指令："))
        self.command_input = QTextEdit()
        self.command_input.setMaximumHeight(100)
        self.main_layout.addWidget(self.command_input)

        # 输出区
        self.main_layout.addWidget(QLabel("输出："))
        self.output_area = OutputArea()
        self.main_layout.addWidget(self.output_area)
