"""托盘图标相关处理"""
from typing import Optional
from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction, QMessageBox
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSignal
from utils.icon import get_icon
from utils.general import log, Path, set_default
from ui.main_window import MainWindow, ICON_NAME


class TrayIcon(QSystemTrayIcon):
    icon_path: Path
    main_window: MainWindow
    pin_action: Optional[QAction] = None

    quit_signal = pyqtSignal()  # 用户要求退出程序

    def __init__(self, main_window: MainWindow, icon_name: Optional[str] = None) -> None:
        super().__init__()
        self.main_window = main_window
        icon_name = set_default(icon_name, ICON_NAME)
        self.icon_path = get_icon(icon_name)

        try:
            self.setIcon(QIcon(self.icon_path))
            tray_menu = QMenu()

            # 显示主窗口
            show_action = tray_menu.addAction("显示主窗口")
            show_action.triggered.connect(self.main_window.show)

            # 置顶/取消置顶
            pin_action = tray_menu.addAction("窗口置顶")
            pin_action.setCheckable(True)
            pin_action.setChecked(self.main_window.pin_flag)
            pin_action.triggered.connect(self.main_window.toggle_pin)
            self.pin_action = pin_action
            # 检测，当主窗口置顶状态更改时更新
            self.main_window.signals.toggle_pin_signal.connect(
                self.on_toggle_pin)

            tray_menu.addSeparator()

            # 退出
            quit_action = tray_menu.addAction("退出")
            quit_action.triggered.connect(self.quit_signal.emit)

            self.setContextMenu(tray_menu)
            self.show()
            def active(reason: QSystemTrayIcon.ActivationReason):
                # 左键点击
                if reason == QSystemTrayIcon.ActivationReason.Trigger:
                    self.main_window.toggle_window()
            self.activated.connect(active)

            if not QSystemTrayIcon.isSystemTrayAvailable():
                QMessageBox.warning(None, "系统托盘不可用", "无法创建托盘图标，程序将在任务栏运行")
                raise RuntimeError("系统托盘不可用")
        except Exception as e:
            log.warning(f"无法创建托盘图标：{e}")
            # 直接展示主窗口
            self.main_window.show()

    def on_toggle_pin(self) -> None:
        """切换置顶状态"""
        if self.pin_action is None:
            log.warning("pin_action 未初始化")
            return
        self.pin_action.setChecked(self.main_window.pin_flag)
