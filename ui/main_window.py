"""
UI 主窗口
"""

from typing import Optional
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QTextEdit, QLabel
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QThread, pyqtSignal
from core.ai_client import ChatContent
from core.assistant import Assistant
from utils.general import set_default, Path, log
from utils.icon import get_icon
from ui.widgets.file_drop_area import FileDropArea
from ui.widgets.file_info import FileInfo
from ui.widgets.output_area import OutputArea
from ui.widgets.model_selector import ModelSelector
from ui.widgets.control_buttons import ControlButtons

WINDOW_TITLE = "智能助手"
MIN_WINDOW_SIZE = (600, 500)
ICON_NAME = "assistant_icon"


class AITaskThread(QThread):
    """在另外的线程等待 AI 回应"""

    finished_signal = pyqtSignal()
    receive_text_signal = pyqtSignal(str)
    confirm_script_signal = pyqtSignal(str)

    is_thinking: bool = False

    assistant: Assistant
    prompt: str

    def add_content(self, content: ChatContent) -> None:
        log.debug(f"on_run_clicked::Context::add_content: {content.text}")
        if content.type == ChatContent.Type.REASONING:
            if not self.is_thinking:
                self.receive_text_signal.emit("<think>")
                self.is_thinking = True
            self.receive_text_signal.emit(content.text)
        elif content.type == ChatContent.Type.CONTENT:
            if self.is_thinking:
                self.receive_text_signal.emit("</think>")
                self.is_thinking = False
            self.receive_text_signal.emit(content.text)
        else:
            self.receive_text_signal.emit(content.text)

    def confirm_script(self, script: str) -> None:
        log.info(f"正在执行脚本: {script}")
        self.confirm_script_signal.emit(script)

    def __init__(self, assistant: Assistant, prompt: str) -> None:
        super().__init__()
        self.assistant = assistant
        self.prompt = prompt

    def run(self) -> None:
        self.assistant.command_signals.confirm_script.connect(
            self.confirm_script)
        self.assistant.command_signals.receive_content.connect(
            self.add_content)
        self.assistant.execute_command(self.prompt)
        self.receive_text_signal.emit("\n命令执行完毕。\n")
        self.finished.emit()

    def cancel(self) -> None:
        self.assistant.command_signals.running_lock = False


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
    model_selector: ModelSelector
    control_buttons: ControlButtons
    output_area: OutputArea

    ai_task_thread: Optional[AITaskThread] = None  # 等待 AI 回应的线程

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

        # 模型选择区
        self.model_selector = ModelSelector()
        self.main_layout.addLayout(self.model_selector)
        self.model_selector.update_model_list(
            [x.name for x in self.assistant.get_models()])

        # 控制按钮
        self.control_buttons = ControlButtons()
        self.control_buttons.execute_command_signal.connect(
            self.execute_command)
        self.control_buttons.stop_command_signal.connect(self.stop_command)
        self.control_buttons.confirm_script_signal.connect(self.confirm_script)
        self.control_buttons.deny_script_signal.connect(self.deny_script)
        self.main_layout.addLayout(self.control_buttons)

        # 输出区
        self.main_layout.addWidget(QLabel("输出："))
        self.output_area = OutputArea()
        self.main_layout.addWidget(self.output_area)

    def execute_command(self):
        """开始执行用户命令"""
        log.debug(f"execute_command")
        command = self.command_input.toPlainText()
        models = self.assistant.get_models()
        current_model = models[self.model_selector.get_selected_index()]
        prompt = self.assistant.build_prompt(
            command, self.assistant.selected_files, current_model.supports_functions)

        # 创建新的进程
        self.ai_task_thread = AITaskThread(self.assistant, prompt)

        def on_finished() -> None:
            self.ai_task_thread = None

        def on_receive_text(text: str) -> None:
            self.output_area.append_text(text)

        def on_confirm(script: str) -> None:
            self.output_area.append_text("\n检测到 Python 脚本：\n")
            self.output_area.append_text(script)
            self.control_buttons.to_confirm_script_mode(script)

        self.ai_task_thread.finished.connect(on_finished)
        self.ai_task_thread.receive_text_signal.connect(on_receive_text)
        self.ai_task_thread.confirm_script_signal.connect(
            on_confirm)  # 切换到确认脚本模式

        self.ai_task_thread.start()

    def stop_command(self):
        """中断用户命令"""
        if self.ai_task_thread is not None:
            self.ai_task_thread.cancel()

    def confirm_script(self, script: str) -> None:
        """确认脚本"""
        self.assistant.process_files(
            script, self.assistant.selected_files, self.output_area.append_text)

    def deny_script(self):
        """拒绝脚本"""
        self.output_area.append_text("未运行脚本")
