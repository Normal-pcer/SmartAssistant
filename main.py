"""
启动主程序
"""
from PyQt5.QtWidgets import QApplication
from core.assistant import Assistant
from ui.main_window import MainWindow
from sys import argv, exit
from ui.tray import TrayIcon
from utils.windows import set_app_id
from utils.general import log
from ui.font import DefaultFont

APP_NAME = "智能助手"
APP_TITLE = "智能助手"
APP_ID = "Normalpcer.SmartAssistant"


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

    app.setFont(DefaultFont())

    # 创建主窗口
    window = MainWindow(Assistant())
    window.show()

    # 创建托盘图标
    tray = TrayIcon(window)
    tray.show()

    # 接管退出事件
    tray.quit_signal.connect(app.quit)

    # 开始运行
    exit(app.exec_())


if __name__ == "__main__":
    main()
