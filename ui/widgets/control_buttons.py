from PyQt5.QtWidgets import QHBoxLayout, QPushButton
from PyQt5.QtCore import pyqtSignal
from typing import Optional
from utils.general import log

class ControlButtons(QHBoxLayout):
    """「运行」和「停止」按钮"""
    run_button: QPushButton
    stop_button: QPushButton

    script_to_run: Optional[str] = None  # 下一步是确认脚本

    execute_command_signal = pyqtSignal()  # 运行命令
    stop_command_signal = pyqtSignal()  # 停止命令
    confirm_script_signal = pyqtSignal(str)  # 确认脚本
    deny_script_signal = pyqtSignal()  # 取消脚本

    def __init__(self) -> None:
        super().__init__()
        self.run_button = QPushButton("运行")
        self.addWidget(self.run_button)
        self.stop_button = QPushButton("停止")
        self.addWidget(self.stop_button)

        self.run_button.clicked.connect(self.on_run_button_clicked)
        self.stop_button.clicked.connect(self.on_stop_button_clicked)
        self.run_button.setStyleSheet("background-color: #4CAF50; color: white;")
        self.stop_button.setStyleSheet("background-color: #F44336; color: white;")
    
    def to_confirm_script_mode(self, script: str) -> None:
        """切换到确认脚本模式"""
        self.script_to_run = script
        self.run_button.setText("确认执行")
        self.stop_button.setText("取消")
    
    def to_normal_mode(self) -> None:
        """切换到正常模式"""
        self.script_to_run = None
        self.run_button.setText("运行")
        self.stop_button.setText("停止")
    
    def is_normal_mode(self) -> bool:
        return self.script_to_run is None
    
    def on_run_button_clicked(self) -> None:
        if self.is_normal_mode():
            self.execute_command_signal.emit()
        else:
            if self.script_to_run is None:
                log.error("ControlButtons.on_run_button_clicked: 没有需要确认的脚本。")
                raise RuntimeError("没有需要确认的脚本。")
            self.confirm_script_signal.emit(self.script_to_run)

    def on_stop_button_clicked(self) -> None:
        if self.is_normal_mode():
            self.stop_command_signal.emit()
        else:
            self.deny_script_signal.emit()
