"""
启动主程序
"""
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from core.assistant import Assistant
from ui.main_window import MainWindow
from sys import argv, exit
from utils.windows import set_app_id
from utils.general import log
from utils.icon import create_default_icon, get_icon

APP_NAME = "智能助手"
APP_TITLE = "智能助手"
APP_ID = "Normalpcer.SmartAssistant"
ICON_NAME = "assistant_icon"

def main():
    # 创建应用实例
    app = QApplication(argv)

    # 设置应用元数据
    app.setApplicationName(APP_NAME)
    app.setApplicationDisplayName(APP_NAME)

    # Windows 特有：设置应用ID
    try:
        set_app_id(APP_ID)
    except Exception as e:
        log.error(f"无法设置 Windows 应用 ID：{e}")
    
    # 创建主窗口
    window = MainWindow(Assistant())

    icon_path = get_icon(ICON_NAME)
    if os.path.exists(icon_path):
        window.setWindowIcon(QIcon(icon_path))
    else:
        window.setWindowIcon(QIcon(create_default_icon()))
    
    window.setWindowTitle(APP_TITLE)

    # 开始运行
    exit(app.exec_())
