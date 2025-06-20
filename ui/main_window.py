"""
UI 主窗口
"""
import threading
from typing import Optional
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QTextEdit, QLabel, QPushButton
from PyQt5.QtGui import QIcon, QCloseEvent
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QObject
from core.ai_client import ChatContent
from core.assistant import Assistant
from utils.general import set_default, Path, log
from utils.icon import get_icon
from ui.widgets.file_drop_area import FileDropArea
from ui.widgets.output_area import OutputArea
from ui.widgets.model_selector import ModelSelector
from ui.widgets.control_buttons import ControlButtons
from ui.stylesheet import STYLESHEET
from utils.keyboard import Hotkey

WINDOW_TITLE = "智能助手"
MIN_WINDOW_SIZE = (600, 500)
ICON_NAME = "assistant_icon"


class AITaskThread(QThread):
    """在另外的线程等待 AI 回应"""

    finished_signal = pyqtSignal()
    receive_text_signal = pyqtSignal(str)
    confirm_script_signal = pyqtSignal(str)

    is_thinking: bool

    assistant: Assistant
    prompt: str

    def __init__(self, assistant: Assistant, prompt: str) -> None:
        super().__init__()
        self.assistant = assistant
        self.prompt = prompt
        self.is_thinking = False

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
    pin_flag: bool = True  # 当前是否置顶

    main_layout: QVBoxLayout
    main_widget: QWidget

    pin_button: QPushButton
    file_drop_area: FileDropArea
    model_selector: ModelSelector
    control_buttons: ControlButtons
    output_area: OutputArea

    ai_task_thread: Optional[AITaskThread] = None  # 等待 AI 回应的线程
    hotkey: Hotkey

    class Signals(QObject):
        toggle_pin_signal = pyqtSignal()
    signals: Signals

    def __init__(self, assis: Optional[Assistant] = None) -> None:
        """
        assis: 传入指定的逻辑处理器
        """
        assis = set_default(assis, Assistant())
        self.assistant = assis
        self.signals = MainWindow.Signals()

        # 初始化窗体
        super().__init__()
        self.setWindowTitle(WINDOW_TITLE)
        self.setMinimumSize(*MIN_WINDOW_SIZE)
        self.setWindowIcon(QIcon(get_icon(ICON_NAME)))

        # 设置样式
        self.setStyleSheet(STYLESHEET)
        # self.setFont(DefaultFont())

        # 创建初始布局
        self.main_widget = QWidget()
        self.main_layout = QVBoxLayout(self.main_widget)
        self.setCentralWidget(self.main_widget)

        # 添加初始组件
        # 工具栏
        self.tool_bar = self.addToolBar("工具栏")
        self.tool_bar.setMovable(False)

        # 置顶按钮
        self.pin_flag = True
        self.pin_button = QPushButton(("置顶", "取消置顶")[self.pin_flag])
        self.pin_button.setCheckable(True)
        self.pin_button.setChecked(self.pin_flag)
        self.pin_button.clicked.connect(self.toggle_pin)
        self.tool_bar.addWidget(self.pin_button)
        self.after_pin()

        # 文件拖放区
        self.file_drop_area = FileDropArea()
        self.main_layout.addWidget(self.file_drop_area)
        self.setAcceptDrops(True )
        def on_add_file(file_path: Path):  # 添加文件时进行相关处理
            log.debug(f"on_add_file: {file_path}")
            self.assistant.selected_files.append(file_path)
        def on_remove_file(file_path: Path):  # 删除文件
            log.debug(f"on_remove_file: {file_path}")
            self.assistant.selected_files.remove(file_path)
        self.file_drop_area.add_file_signal.connect(on_add_file)
        self.file_drop_area.remove_file_signal.connect(on_remove_file)

        # 命令输入区
        self.main_layout.addWidget(QLabel("指令："))
        self.command_input = QTextEdit()
        self.command_input.setMaximumHeight(100)
        self.main_layout.addWidget(self.command_input)

        # 模型选择区
        self.model_selector = ModelSelector(self, self.assistant)
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

        # 设置快捷键
        self.hotkey = Hotkey("<ctrl>+<alt>+<space>")
        self.hotkey.signal.connect(self.toggle_window)
        thread = threading.Thread(target=self.hotkey.listen, daemon=True)
        thread.start()

    def toggle_window(self) -> None:
        if self.isVisible():
            self.hide()
        else:
            self.show()

    def execute_command(self) -> None:
        """开始执行用户命令"""
        log.debug(f"execute_command")
        self.output_area.append_text("开始执行用户命令。\n")
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

    def stop_command(self) -> None:
        """中断用户命令"""
        if self.ai_task_thread is not None:
            self.ai_task_thread.cancel()

    def confirm_script(self, script: str) -> None:
        """确认脚本"""
        self.assistant.process_files(
            script, self.assistant.selected_files, self.output_area.append_text)
        self.control_buttons.to_normal_mode()

    def deny_script(self) -> None:
        """拒绝脚本"""
        self.output_area.append_text("未运行脚本")
        self.control_buttons.to_normal_mode()

    def toggle_pin(self) -> None:
        """切换置顶状态"""
        text = ("置顶", "取消置顶")
        self.pin_flag = not self.pin_flag
        self.pin_button.setText(text[self.pin_flag])
        self.pin_button.setChecked(self.pin_flag)
        self.after_pin()
        self.show()
        self.signals.toggle_pin_signal.emit()

    def after_pin(self) -> None:
        """置顶或取消置顶后，重新设置窗口状态"""
        if self.pin_flag:
            self.setWindowFlags(self.windowFlags() |
                                Qt.WindowType.WindowStaysOnTopHint)
            self.statusBar().showMessage("窗口已置顶", 2000)
        else:
            self.setWindowFlags(self.windowFlags() & ~
                                Qt.WindowType.WindowStaysOnTopHint)
            self.statusBar().showMessage("窗口已取消置顶", 2000)

    def closeEvent(self, a0: Optional[QCloseEvent]) -> None:
        """重写关闭事件，在后台持续运行"""
        if a0 is None:
            return
        event = a0
        event.ignore()
        self.hide()