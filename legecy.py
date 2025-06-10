import sys
import os
import re
import subprocess
import tempfile
import json
import mimetypes
import time
import platform
import threading
from PyQt5.QtWidgets import (QApplication, QMainWindow, QSystemTrayIcon, QMenu,
                             QStyle, QVBoxLayout, QWidget, QLineEdit, QPushButton,
                             QLabel, QTextEdit, QListWidget, QMessageBox,
                             QHBoxLayout, QComboBox, QSpacerItem, QSizePolicy,
                             QDialog, QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt5.QtCore import Qt, QObject, pyqtSignal, QPropertyAnimation
from PyQt5.QtGui import QIcon, QFont, QDragEnterEvent, QDropEvent, QTextCursor, QKeyEvent, QCloseEvent
from openai import OpenAI

ICON_PATH = "assistant_icon"  # 图标基础名称


def set_windows_app_id():
    if platform.system() == "Windows":
        try:
            from ctypes import windll
            # 设置唯一的应用ID
            app_id = "DeepSeek.SmartAssistant.1"
            windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
        except:
            print("无法设置 Windows 应用 ID。")


def create_default_icon():
    """创建默认应用图标"""
    try:
        from PIL import Image, ImageDraw
        img = Image.new('RGB', (64, 64), color=(70, 130, 180))
        d = ImageDraw.Draw(img)
        d.text((10, 25), "AI", fill=(255, 255, 255))
        temp_icon = os.path.join(
            tempfile.gettempdir(), "assistant_temp_icon.ico")
        img.save(temp_icon)
        return temp_icon
    except ImportError:
        return None


class GlobalSignals(QObject):
    toggle_window_signal = pyqtSignal()
    show_window_signal = pyqtSignal()
    hide_window_signal = pyqtSignal()
    toggle_always_on_top = pyqtSignal()  # 新增置顶切换信号


class SmartAssistant(QMainWindow):
    """智能助手主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("智能助手")
        self.setMinimumSize(600, 500)

        # 创建信号对象
        self.signals = GlobalSignals()

        # 连接信号
        self.signals.toggle_window_signal.connect(self.toggle_window)
        self.signals.show_window_signal.connect(self.show_normal)
        self.signals.hide_window_signal.connect(self.hide)
        self.signals.toggle_always_on_top.connect(self.toggle_always_on_top)

        # 尝试加载图标
        try:
            self.setWindowIcon(QIcon(self.get_icon_path("assistant_icon")))
        except:
            pass

        # 窗口置顶状态
        self.is_always_on_top = True

        # 初始化AI客户端
        self.client = self.init_ai_client()

        # 创建系统托盘
        self.create_tray_icon()

        # 主界面布局
        self.init_ui()

        # 历史记录
        self.history = []
        self.load_history()

        # 设置全局快捷键
        self.setup_global_hotkey()

        # 创建状态栏
        if bar := self.statusBar():
            bar.showMessage("就绪")

        # 显示当前模型信息
        self.update_model_status()

        # 设置窗口标志
        self.setWindowFlags(Qt.WindowType(Qt.WindowType.Window |
                            Qt.WindowType.WindowStaysOnTopHint))

    def init_ai_client(self):
        """初始化兼容OpenAI API的客户端（支持DeepSeek等平台）"""
        config = self.load_config()
        api_key = config.get('api_key', '')
        api_base = config.get(
            'api_base', 'https://api.openai.com/v1')  # 默认OpenAI地址

        return OpenAI(api_key=api_key, base_url=api_base)

    def apply_styles(self):
        """应用全局样式"""
        # 合并所有样式到一个字符串中
        stylesheet = """
            /* 主窗口样式 */
            QMainWindow {
                background-color: #f5f5f5;
                font-family: 'PingFang SC', 'Noto Sans', 'Noto Sans SC', 'Source Sans Pro', 
                            'Segoe UI', Arial, 'Microsoft YaHei', 'WenQuanYi Micro Hei', sans-serif;
            }
            
            /* 标签样式 */
            QLabel {
                font-weight: bold;
                color: #333;
                font-size: 11pt;
            }
            
            /* 输入框样式 */
            QTextEdit, QListWidget, QComboBox, QLineEdit {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 6px;
                font-size: 10pt;
            }
            
            /* 按钮基础样式 */
            QPushButton {
                min-height: 32px;
                min-width: 80px;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: 500;
                font-size: 10pt;
            }
            
            /* 主执行按钮 */
            QPushButton[text="执行"] {
                background-color: #4CAF50;
                color: white;
            }
            
            /* 历史记录按钮 */
            QPushButton[text="历史"] {
                background-color: #2196F3;
                color: white;
            }
            
            /* 配置按钮 */
            QPushButton[text="配置"] {
                background-color: #9E9E9E;
                color: white;
            }
            
            /* 脚本执行按钮 */
            QPushButton[text="执行脚本"] {
                background-color: #4CAF50;
                color: white;
            }
            
            /* 文件生成按钮 */
            QPushButton[text^="生成文件:"] {
                background-color: #FF9800;
                color: white;
                text-align: left;
                padding-left: 8px;
            }
            
            /* 删除按钮 */
            QPushButton[text="删除"] {
                background-color: #F44336;
                color: white;
            }
            
            /* 悬停效果 */
            QPushButton:hover {
                opacity: 0.9;
            }
            
            /* 按下效果 */
            QPushButton:pressed {
                opacity: 0.8;
            }
            
            /* 禁用状态 */
            QPushButton:disabled {
                background-color: #BDBDBD;
                color: #757575;
            }
            
            /* 进度条样式 */
            QProgressBar {
                border: 1px solid #ccc;
                border-radius: 4px;
                text-align: center;
                font-size: 9pt;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
            }
            
            /* 表格样式 */
            QTableWidget {
                background-color: white;
                border: 1px solid #ddd;
                font-size: 10pt;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                padding: 6px;
                border: none;
                font-weight: bold;
            }
            
            /* 状态栏样式 */
            QStatusBar {
                background-color: #e0e0e0;
                color: #333;
                font-size: 9pt;
                padding: 2px 8px;
            }
        """

        # 一次性设置所有样式
        self.setStyleSheet(stylesheet)

        # 设置全局字体
        app_font = QFont("Microsoft YaHei UI", 9)  # 使用微软雅黑作为首选字体
        QApplication.setFont(app_font)

    def load_config(self):
        """加载配置文件"""
        config_path = os.path.expanduser("~/.smart_assistant/config.json")

        # 默认配置
        default_config = {
            "models": [
                {
                    "name": "GPT-4 Turbo",
                    "model_id": "gpt-4-turbo",
                    "api_base": "https://api.openai.com/v1",
                    "api_key": "",
                    "supports_functions": True
                }
            ],
            "current_model_index": 0
        }

        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    user_config = json.load(f)

                    # 确保结构完整
                    if "models" not in user_config:
                        user_config["models"] = default_config["models"]

                    if "current_model_index" not in user_config:
                        user_config["current_model_index"] = 0

                    # 确保当前索引有效
                    current_index = user_config["current_model_index"]
                    if current_index >= len(user_config["models"]):
                        user_config["current_model_index"] = 0

                    return user_config
            except Exception as e:
                print(f"加载配置错误: {str(e)}")
                return default_config
        return default_config

    def save_config(self, config=None):
        """保存配置文件"""
        if config is None:
            config = self.load_config()

        config_path = os.path.expanduser("~/.smart_assistant/config.json")
        os.makedirs(os.path.dirname(config_path), exist_ok=True)

        try:
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            return True
        except Exception as e:
            QMessageBox.warning(self, "保存错误", f"无法保存配置: {str(e)}")
            return False

    def get_icon_path(self, base_name):
        """获取图标路径，支持多种格式"""
        for ext in [".png", ".ico", ".svg"]:
            path = f"{base_name}{ext}"
            if os.path.exists(path):
                return path
        # 如果找不到文件，创建临时图标
        return self.create_temp_icon()

    def create_temp_icon(self):
        """创建临时图标文件"""
        try:
            from PIL import Image, ImageDraw
            img = Image.new('RGB', (64, 64), color=(70, 130, 180))
            d = ImageDraw.Draw(img)
            d.text((10, 25), "AI", fill=(255, 255, 255))
            temp_path = os.path.join(tempfile.gettempdir(), "temp_icon.png")
            img.save(temp_path)
            return temp_path
        except ImportError:
            return ""

    def create_tray_icon(self):
        try:
            self.tray_icon = QSystemTrayIcon(self)

            # 尝试加载托盘图标
            tray_icon_path = self.get_icon_path(ICON_PATH)
            if tray_icon_path and os.path.exists(tray_icon_path):
                self.tray_icon.setIcon(QIcon(tray_icon_path))
            elif style := self.style():
                self.tray_icon.setIcon(
                    style.standardIcon(QStyle.StandardPixmap.SP_ComputerIcon))

            tray_menu = QMenu()

            # 显示主窗口
            if show_action := tray_menu.addAction("显示主窗口"):
                show_action.triggered.connect(self.show_normal)

            # 置顶/取消置顶
            if topmost_action := tray_menu.addAction("窗口置顶"):
                self.topmost_action = topmost_action
                self.topmost_action.setCheckable(True)
                self.topmost_action.setChecked(self.is_always_on_top)
                self.topmost_action.triggered.connect(
                    self.toggle_always_on_top)

            tray_menu.addSeparator()

            # 退出
            if quit_action := tray_menu.addAction("退出"):
                quit_action.triggered.connect(self.quit_app)

            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.show()
            self.tray_icon.activated.connect(self.tray_icon_activated)

            # 检查托盘是否可用
            if not QSystemTrayIcon.isSystemTrayAvailable():
                QMessageBox.warning(None, "系统托盘不可用",
                                    "您的系统不支持托盘图标，程序将在任务栏运行")
                self.show()
        except Exception as e:
            print(f"创建托盘图标失败: {str(e)}")
            self.show()

    def show_normal(self):
        """正常显示窗口并确保置顶"""
        # 确保窗口显示在屏幕中央
        if p_screen := QApplication.primaryScreen():
            screen = p_screen.geometry()
        else:
            QMessageBox.warning(
                self, "显示错误", "无法获取主屏幕信息，窗口将无法正确显示")
            return
        window_size = self.size()
        self.move(
            int((screen.width() - window_size.width()) / 2),
            int((screen.height() - window_size.height()) / 3)
        )

        # 显示窗口（带淡入效果）
        self.setWindowOpacity(0.0)
        self.show()

        # 创建动画
        self.animation = QPropertyAnimation(self, b"windowOpacity")
        self.animation.setDuration(200)  # 200毫秒
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.start(
            QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)

        # 激活窗口
        self.activateWindow()
        self.raise_()

        # 确保窗口在最前面
        self.setWindowState(Qt.WindowState(self.windowState() & ~
                            Qt.WindowState.WindowMinimized | Qt.WindowState.WindowActive))

        # 更新窗口置顶标志
        if self.is_always_on_top:
            self.setWindowFlags(self.windowFlags() |
                                Qt.WindowType.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(Qt.WindowType(self.windowFlags() & ~
                                Qt.WindowType.WindowStaysOnTopHint))

        # 重新显示窗口以应用标志
        self.show()

        # 将焦点设置到指令输入框
        self.command_input.setFocus()

        # 清除上次的内容
        self.file_info.clear()
        self.file_preview.clear()
        self.command_input.clear()
        self.output_area.clear()

    def register_hotkey(self):
        """注册全局快捷键"""
        hotkey = "ctrl+alt+space"
        print(f"尝试注册全局快捷键: {hotkey}")

        if platform.system() == "Windows":
            try:
                import keyboard as kb

                # Windows平台
                kb.add_hotkey(
                    hotkey, lambda: self.signals.toggle_window_signal.emit())
                print(f"成功注册快捷键: {hotkey}")

                # 保持线程运行
                while True:
                    time.sleep(1)
            except Exception as e:
                print(f"快捷键注册失败: {str(e)}")

        elif platform.system() == "Darwin":
            # macOS平台
            try:
                from pynput import keyboard

                def on_activate():
                    self.signals.toggle_window_signal.emit()

                listener = keyboard.GlobalHotKeys({
                    '<ctrl>+<alt>+space': on_activate
                })
                listener.start()
                print(f"成功注册快捷键: {hotkey}")

                # 保持线程运行
                while True:
                    time.sleep(1)
            except Exception as e:
                print(f"macOS快捷键注册失败: {str(e)}")

        elif platform.system() == "Linux":
            # Linux平台 (DBus实现)
            import dbus  # type: ignore
            import dbus.service  # type: ignore
            import dbus.mainloop.glib  # type: ignore
            from gi.repository import GLib  # type: ignore

            try:
                dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
                bus = dbus.SessionBus()
                # 尝试注册服务
                bus_name = dbus.service.BusName(
                    "com.example.SmartAssistant", bus)
                service = HotkeyService(
                    bus, '/Hotkeys', lambda: self.signals.toggle_window_signal.emit())
                print("DBus服务已启动，等待快捷键注册...")

                # 启动事件循环
                loop = GLib.MainLoop()
                loop.run()
            except Exception as e:
                print(f"Linux快捷键注册失败: {str(e)}")

    def toggle_window(self):
        """切换窗口显示状态（在主线程中执行）"""
        if self.isVisible():
            self.hide()
        else:
            self.show_normal()

    def toggle_always_on_top(self):
        """切换窗口置顶状态"""
        self.is_always_on_top = not self.is_always_on_top

        # 更新窗口标志
        if self.is_always_on_top:
            self.setWindowFlags(self.windowFlags() |
                                Qt.WindowType.WindowStaysOnTopHint)
            if bar := self.statusBar():
                bar.showMessage("窗口已置顶", 2000)
        else:
            self.setWindowFlags(Qt.WindowType(self.windowFlags() & ~
                                Qt.WindowType.WindowStaysOnTopHint))
            if bar := self.statusBar():
                bar.showMessage("窗口已取消置顶", 2000)

        # 重新显示窗口以应用标志
        self.show()

        # 更新置顶按钮状态
        self.update_pin_button_icon()

        # 更新托盘菜单状态
        if hasattr(self, 'topmost_action'):
            self.topmost_action.setChecked(self.is_always_on_top)

    def setup_global_hotkey(self):
        """设置全局快捷键"""
        # 使用线程避免阻塞主线程
        hotkey_thread = threading.Thread(
            target=self.register_hotkey, daemon=True)
        hotkey_thread.start()

    def keyPressEvent(self, a0: QKeyEvent | None):
        """处理键盘事件"""
        event = a0
        if event is None:
            return

        # 按 ESC 键隐藏窗口
        if event.key() == Qt.Key.Key_Escape:
            self.hide()

        # 按 Ctrl+T 切换置顶状态
        elif event.key() == Qt.Key.Key_T and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.toggle_always_on_top()

        super().keyPressEvent(event)

    def tray_icon_activated(self, reason):
        """托盘图标点击事件处理"""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:  # 左键点击
            self.toggle_window()

    def init_ui(self):
        main_widget = QWidget()
        layout = QVBoxLayout(main_widget)
        layout.setSpacing(10)  # 减少控件间距
        layout.setContentsMargins(15, 15, 15, 15)  # 适当的内边距

        # 文件拖放区
        self.file_drop_area = QLabel("拖拽文件到这里")
        self.file_drop_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.file_drop_area.setStyleSheet(
            "border: 2px dashed #aaa; border-radius: 10px; padding: 20px;"
            "background-color: #f9f9f9; font-size: 16px;"
        )
        self.file_drop_area.setAcceptDrops(True)
        self.file_drop_area.setMinimumHeight(100)
        layout.addWidget(self.file_drop_area)

        # 文件信息显示
        self.file_info = QListWidget()
        self.file_info.setMaximumHeight(100)
        self.file_info.setStyleSheet("font-size: 12px;")
        layout.addWidget(QLabel("已添加文件:"))
        layout.addWidget(self.file_info)

        # 文件预览区域（只读）
        file_preview_layout = QVBoxLayout()
        file_preview_layout.setContentsMargins(0, 0, 0, 0)

        preview_label = QLabel("文件预览:")
        preview_label.setStyleSheet("font-weight: bold; margin-bottom: 4px;")
        file_preview_layout.addWidget(preview_label)

        self.file_preview = QTextEdit()
        self.file_preview.setReadOnly(True)
        self.file_preview.setStyleSheet("""
            background-color: #f8f9fa;
            border: 1px solid #e0e0e0;
            border-radius: 4px;
            padding: 6px;
            font-size: 13px;
        """)
        self.file_preview.setMaximumHeight(120)  # 限制高度
        file_preview_layout.addWidget(self.file_preview)

        layout.addLayout(file_preview_layout)

        # 指令输入区域（用户可编辑）
        layout.addWidget(QLabel("指令:"))
        self.command_input = QTextEdit()
        self.command_input.setPlaceholderText("输入您的指令...")
        self.command_input.setStyleSheet("""
            background-color: #ffffff;
            border: 1px solid #e0e0e0;
            border-radius: 5px;
            padding: 8px;
            font-size: 14px;
        """)

        self.command_input.setMaximumHeight(100)
        layout.addWidget(self.command_input)
        # 操作按钮
        btn_layout = QHBoxLayout()

        self.execute_btn = QPushButton("执行")
        self.execute_btn.setFixedSize(100, 36)  # 固定宽度和高度
        self.execute_btn.setStyleSheet(
            "background-color: #4CAF50; color: white; font-weight: bold;"
        )
        self.execute_btn.clicked.connect(self.execute_command)
        btn_layout.addWidget(self.execute_btn)

        self.history_btn = QPushButton("历史")
        self.history_btn.setFixedSize(80, 36)
        self.history_btn.setStyleSheet(
            "background-color: #2196F3; color: white;"
        )
        self.history_btn.clicked.connect(self.show_history)
        btn_layout.addWidget(self.history_btn)

        # 添加一个间隔，使按钮组靠右
        btn_layout.addStretch()

        layout.addLayout(btn_layout)

        # 模型选择区域
        model_layout = QHBoxLayout()
        model_layout.setContentsMargins(0, 0, 0, 0)

        model_label = QLabel("模型:")
        model_label.setStyleSheet("font-weight: bold;")
        model_layout.addWidget(model_label)

        self.model_combo = QComboBox()
        self.model_combo.setMinimumWidth(200)
        self.model_combo.setStyleSheet("""
            QComboBox {
                padding: 4px;
            }
        """)
        model_layout.addWidget(self.model_combo)

        model_layout.addStretch()

        self.config_button = QPushButton("配置")
        self.config_button.setFixedSize(60, 28)  # 更小尺寸
        self.config_button.setStyleSheet(
            "background-color: #9E9E9E; color: white;")
        self.config_button.setToolTip("打开配置窗口")
        self.config_button.clicked.connect(self.open_config_dialog)
        model_layout.addWidget(self.config_button)

        layout.addLayout(model_layout)

        # 添加分隔符
        model_layout.addSpacerItem(QSpacerItem(
            20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        # 添加模型选择区域到主布局
        layout.addLayout(model_layout)

        # 输出区域
        layout.addWidget(QLabel("执行结果:"))
        self.output_area = QTextEdit()
        self.output_area.setReadOnly(True)
        self.output_area.setStyleSheet("background-color: #f0f0f0;")
        layout.addWidget(self.output_area)

        main_widget.setLayout(layout)
        self.setCentralWidget(main_widget)

        # 设置拖拽支持
        self.setAcceptDrops(True)

        # 应用样式
        self.apply_styles()

        # 添加置顶按钮到工具栏
        if bar := self.addToolBar("工具栏"):
            self.toolbar = bar
            self.toolbar.setMovable(False)

        # 置顶按钮
        self.pin_button = QPushButton()
        self.pin_button.setCheckable(True)
        self.pin_button.setChecked(self.is_always_on_top)
        self.pin_button.setToolTip("窗口置顶 (Ctrl+T)")
        self.pin_button.clicked.connect(self.toggle_always_on_top)
        self.toolbar.addWidget(self.pin_button)

        # 更新置顶按钮图标
        self.update_pin_button_icon()

        self.load_model_list()

    def update_pin_button_icon(self):
        """更新置顶按钮图标"""
        if self.is_always_on_top:
            self.pin_button.setIcon(QIcon.fromTheme("pin"))
            self.pin_button.setText("取消置顶")
        else:
            self.pin_button.setIcon(QIcon.fromTheme("unpin"))
            self.pin_button.setText("窗口置顶")

    def load_model_list(self):
        """从配置加载模型列表并更新下拉框"""
        config = self.load_config()
        models = config.get("models", [])

        # 清空当前列表
        self.model_combo.clear()

        # 添加模型选项
        for model in models:
            self.model_combo.addItem(model["name"], model["model_id"])

        # 设置当前选择
        current_index = config.get("current_model_index", 0)
        if current_index < self.model_combo.count():
            self.model_combo.setCurrentIndex(current_index)

        # 连接选择变化信号
        self.model_combo.currentIndexChanged.connect(
            self.model_selection_changed)

    def model_selection_changed(self, index: int):
        """当用户选择不同模型时更新配置"""
        if index >= 0:
            # 更新配置中的当前模型索引
            config = self.load_config()
            config["current_model_index"] = index
            self.save_config(config)

            # 更新状态栏提示
            current_model = config["models"][index]
            model_name = current_model["name"]
            supports_fc = "支持" if current_model.get(
                "supports_functions", False) else "不支持"
            if bar := self.statusBar():
                bar.showMessage(
                    f"当前模型: {model_name} | Function Calling: {supports_fc}")

    def open_config_dialog(self):
        """打开模型配置对话框"""
        dialog = QDialog(self)
        dialog.setWindowTitle("模型配置")
        dialog.setMinimumSize(700, 500)

        layout = QVBoxLayout(dialog)

        # 模型列表表格
        self.model_table = QTableWidget()
        self.model_table.setColumnCount(6)
        self.model_table.setHorizontalHeaderLabels(
            ["名称", "模型ID", "API地址", "API密钥", "支持Function Calling", "操作"])
        if header := self.model_table.horizontalHeader():
            header.setSectionResizeMode(QHeaderView.Interactive)
            header.setSectionResizeMode(0, QHeaderView.Stretch)  # 名称列自适应
            header.setSectionResizeMode(
                1, QHeaderView.ResizeToContents)  # 模型ID固定宽度
            header.setSectionResizeMode(2, QHeaderView.Stretch)  # API地址自适应
            header.setSectionResizeMode(3, QHeaderView.Stretch)  # API密钥自适应
            header.setSectionResizeMode(
                4, QHeaderView.ResizeToContents)  # 功能支持固定宽度

        # 加载模型数据到表格
        self.populate_model_table()

        layout.addWidget(self.model_table)

        # 按钮区域
        button_layout = QHBoxLayout()

        # 添加模型按钮
        add_button = QPushButton("添加模型")
        add_button.setFixedSize(100, 32)
        add_button.clicked.connect(self.add_model_row)
        button_layout.addWidget(add_button)

        # 保存按钮
        save_button = QPushButton("保存")
        save_button.setFixedSize(80, 32)
        save_button.setStyleSheet("background-color: #4CAF50; color: white;")
        save_button.clicked.connect(lambda: self.save_model_config(dialog))
        button_layout.addWidget(save_button)

        # 取消按钮
        cancel_button = QPushButton("取消")
        cancel_button.setFixedSize(80, 32)
        cancel_button.setStyleSheet("background-color: #9E9E9E; color: white;")
        cancel_button.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)

        dialog.exec_()

        # 设置表格样式
        self.model_table.setStyleSheet("""
            QTableWidget {
                alternate-background-color: #f8f9fa;
            }
            QTableWidget::item {
                padding: 6px;
            }
        """)

    def populate_model_table(self):
        """将模型数据填充到表格中"""
        config = self.load_config()
        models = config.get("models", [])

        self.model_table.setRowCount(len(models))

        for row, model in enumerate(models):
            # 名称
            name_item = QTableWidgetItem(model.get("name", ""))
            self.model_table.setItem(row, 0, name_item)

            # 模型ID
            model_id_item = QTableWidgetItem(model.get("model_id", ""))
            self.model_table.setItem(row, 1, model_id_item)

            # API地址
            api_base_item = QTableWidgetItem(
                model.get("api_base", "https://api.openai.com/v1"))
            self.model_table.setItem(row, 2, api_base_item)

            # API密钥 - 使用LineEdit小部件
            api_key_edit = QLineEdit(model.get("api_key", ""))
            api_key_edit.setEchoMode(QLineEdit.Password)  # 密码模式
            self.model_table.setCellWidget(row, 3, api_key_edit)

            # 支持Function Calling
            supports_fc = model.get("supports_functions", False)
            fc_item = QTableWidgetItem()
            fc_item.setFlags(Qt.ItemFlag(Qt.ItemFlag.ItemIsUserCheckable |
                             Qt.ItemFlag.ItemIsEnabled))
            fc_item.setCheckState(
                Qt.CheckState.Checked if supports_fc else Qt.CheckState.Unchecked)
            self.model_table.setItem(row, 4, fc_item)

            # 删除按钮
            delete_button = QPushButton("删除")
            delete_button.setFixedSize(60, 26)  # 更小的尺寸
            delete_button.setStyleSheet("""
                background-color: #ff6b6b; 
                color: white;
                font-size: 11px;
                padding: 2px 4px;
            """)
            delete_button.clicked.connect(
                lambda _, r=row: self.delete_model_row(r))
            self.model_table.setCellWidget(row, 5, delete_button)

    def add_model_row(self):
        """添加新模型行"""
        row_count = self.model_table.rowCount()
        self.model_table.insertRow(row_count)

        # 添加空数据
        for col in [0, 1, 2]:  # 名称、模型ID、API地址
            self.model_table.setItem(row_count, col, QTableWidgetItem(""))

        # API密钥输入框
        api_key_edit = QLineEdit()
        api_key_edit.setEchoMode(QLineEdit.Password)
        self.model_table.setCellWidget(row_count, 3, api_key_edit)

        # Function Calling复选框
        fc_item = QTableWidgetItem()
        fc_item.setFlags(Qt.ItemFlag(Qt.ItemFlag.ItemIsUserCheckable |
                         Qt.ItemFlag.ItemIsEnabled))
        fc_item.setCheckState(Qt.CheckState.Unchecked)
        self.model_table.setItem(row_count, 4, fc_item)

        # 删除按钮
        delete_button = QPushButton("删除")
        delete_button.setStyleSheet("background-color: #ff6b6b; color: white;")
        delete_button.clicked.connect(
            lambda _, r=row_count: self.delete_model_row(r))
        self.model_table.setCellWidget(row_count, 5, delete_button)

        # 滚动到最后一行
        self.model_table.scrollToBottom()

    def save_model_config(self, dialog):
        """从表格保存模型配置"""
        config = self.load_config()
        models = []

        for row in range(self.model_table.rowCount()):
            # 获取API密钥输入框内容
            api_key_widget = self.model_table.cellWidget(row, 3)
            api_key = api_key_widget.text() if api_key_widget else ""

            def get_text(item: QTableWidgetItem | None) -> str:
                return item.text() if item else ""

            if item := self.model_table.item(row, 4):
                supports_fc = item.checkState() == Qt.CheckState.Checked
            else:
                supports_fc = False

            model = {
                "name": get_text(self.model_table.item(row, 0)),
                "model_id": get_text(self.model_table.item(row, 1)),
                "api_base": get_text(self.model_table.item(row, 2)),
                "api_key": api_key,
                "supports_functions": supports_fc
            }

            # 验证必要字段
            if not model["name"] or not model["model_id"]:
                QMessageBox.warning(self, "配置错误", "模型名称和模型ID不能为空")
                return

            models.append(model)

        # 更新配置
        config["models"] = models

        # 确保当前索引有效
        current_index = config.get("current_model_index", 0)
        if current_index >= len(models):
            config["current_model_index"] = 0

        # 保存配置
        self.save_config(config)

        # 重新加载模型列表
        self.load_model_list()

        # 更新状态栏
        self.update_model_status()

        # 关闭对话框
        dialog.accept()

    def update_model_status(self):
        """更新状态栏中的模型信息"""
        bar = self.statusBar()
        if bar is None:
            return
        config = self.load_config()
        current_index = config.get("current_model_index", 0)
        models = config.get("models", [])

        if current_index < len(models):
            current_model = models[current_index]
            model_name = current_model["name"]
            supports_fc = "FC" if current_model.get(
                "supports_functions", False) else "no-FC"
            bar.showMessage(f"模型: {model_name} ({supports_fc})")
        else:
            bar.showMessage("未选择模型")

    def dragEnterEvent(self, a0: QDragEnterEvent | None):
        """处理拖拽进入事件"""
        if a0 is None:
            return
        event = a0
        if (data := event.mimeData()) and (data.hasUrls()):
            event.acceptProposedAction()

    def dropEvent(self, a0: QDropEvent | None):
        """处理拖拽放下事件"""
        if a0 is None:
            return
        event = a0

        data = event.mimeData()
        if data is None:
            return

        for url in data.urls():
            file_path = url.toLocalFile()
            if os.path.isfile(file_path):
                self.add_file(file_path)
        event.acceptProposedAction()

    def add_file(self, file_path):
        # 添加到文件列表
        self.file_info.addItem(file_path)

        if os.path.getsize(file_path) < 10240:  # 小于10KB
            # 如果是小文本文件，添加到预览区域
            mime = mimetypes.guess_type(file_path)[0]
            if mime and 'text' in mime:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read(1000)  # 只读取前1000个字符
                        self.file_preview.append(
                            f"文件: {os.path.basename(file_path)}")
                        self.file_preview.append(content)
                        self.file_preview.append("-" * 40)
                except Exception:
                    pass
        else:
            # 否则，显示文件名
            self.file_preview.append(
                f"文件: {os.path.basename(file_path)} （无预览）")

    def execute_command(self):
        command = self.command_input.toPlainText().strip()
        if not command:
            QMessageBox.warning(self, "输入错误", "请输入指令")
            return

        # 获取文件列表
        files = []
        for index in range(self.file_info.count()):
            if item := self.file_info.item(index):
                files.append(item.text())

        # 获取当前配置
        config = self.load_config()
        current_index = config.get("current_model_index", 0)
        models = config.get("models", [])

        if current_index < len(models):
            current_model = models[current_index]
            model_id = str(current_model["model_id"])
            api_base = str(current_model["api_base"])
            api_key = str(current_model["api_key"])
            supports_functions = bool(
                current_model.get("supports_functions", False))

            # 设置客户端
            self.client.api_key = api_key
            self.client.base_url = api_base

            # 在输出区域显示使用的模型
            self.output_area.append(f"使用模型: {model_id}")
            if supports_functions:
                self.output_area.append("模式: Function Calling")
            else:
                self.output_area.append("模式: 无 Function Calling")
        else:
            # 没有可用模型
            self.output_area.append("错误: 没有配置有效的模型")
            return

        # 构建AI提示
        prompt = self.build_prompt(command, files, supports_functions)
        print("execute_command: prompt =", prompt)
        layout = self.layout()
        if layout is None:
            raise RuntimeError("Layout is not initialized")
        # 调用AI
        try:
            self.output_area.append("正在思考解决方案...")
            QApplication.processEvents()  # 更新UI

            # 清空之前的确认按钮
            if hasattr(self, 'confirm_execute_button'):
                if layout := self.layout():
                    layout.removeWidget(self.confirm_execute_button)
                self.confirm_execute_button.deleteLater()
                del self.confirm_execute_button

            file_path = None
            # 根据模型能力选择调用方式
            if supports_functions:
                # 支持Function Calling的模型
                tools = [
                    {
                        "type": "function",
                        "function": {
                            "name": "execute_python_script",
                            "description": "Execute a Python script to process files",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "script": {
                                        "type": "string",
                                        "description": "The Python script code to execute"
                                    }
                                },
                                "required": ["script"]
                            }
                        }
                    },
                    {
                        "type": "function",
                        "function": {
                            "name": "output_direct_result",
                            "description": "Output the result directly without executing code",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "result": {
                                        "type": "string",
                                        "description": "The result to output directly"
                                    }
                                },
                                "required": ["result"]
                            }
                        }
                    },
                    {
                        "type": "function",
                        "function": {
                            "name": "generate_file_content",
                            "description": "Generate new file content directly",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "file_path": {
                                        "type": "string",
                                        "description": "Output file path including extension"
                                    },
                                    "content": {
                                        "type": "string",
                                        "description": "Content to write to the file"
                                    }
                                },
                                "required": ["file_path", "content"]
                            }
                        }
                    }
                ]

                # 流式调用AI
                self.output_area.append("\n使用Function Calling模式...")
                QApplication.processEvents()

                from openai.types.chat.chat_completion_tool_param import ChatCompletionToolParam

                stream = self.client.chat.completions.create(
                    model=model_id,
                    messages=[{"role": "user", "content": prompt}],
                    tools=[ChatCompletionToolParam(**tool) for tool in tools],
                    tool_choice="auto",
                    stream=True,
                    temperature=0.2,
                )

                full_response = ""
                self.output_area.append("AI响应:")

                # 处理流式响应
                tool_calls = None
                for chunk in stream:
                    if chunk.choices:
                        delta = chunk.choices[0].delta

                        # 收集文本内容
                        if delta.content:
                            content_chunk = delta.content
                            full_response += content_chunk
                            self.output_area.moveCursor(QTextCursor.End)
                            self.output_area.insertPlainText(content_chunk)
                            QApplication.processEvents()

                        # 收集工具调用
                        if delta.tool_calls:
                            if tool_calls is None:
                                tool_calls = []

                            for tool_call in delta.tool_calls:
                                idx = tool_call.index
                                if idx >= len(tool_calls):
                                    # 新的工具调用
                                    tool_calls.append({
                                        "id": tool_call.id,
                                        "type": tool_call.type,
                                        "function": {
                                            "name": tool_call.function.name if tool_call.function else "",
                                            "arguments": tool_call.function.arguments if tool_call.function else ""
                                        }
                                    })
                                elif tool_call.function:
                                    # 追加参数
                                    tool_calls[idx]["function"]["arguments"] += tool_call.function.arguments

                # 处理工具调用
                if tool_calls:
                    self.output_area.append("\n\n检测到工具调用:")
                    for tool_call in tool_calls:
                        function_name = tool_call["function"]["name"]
                        arguments = tool_call["function"]["arguments"]

                        self.output_area.append(f"\n工具: {function_name}")
                        self.output_area.append(f"参数: {arguments}")

                        try:
                            # 尝试解析参数
                            args_dict = json.loads(arguments)

                            if function_name == "execute_python_script":
                                script = args_dict["script"]
                                self.output_area.append("\n生成脚本:")
                                self.output_area.append(script)

                                # 添加执行确认按钮
                                self.confirm_execute_button = QPushButton(
                                    "执行脚本")
                                self.confirm_execute_button.setFixedSize(
                                    120, 36)  # 设置固定尺寸
                                self.confirm_execute_button.setStyleSheet(
                                    "background-color: #4CAF50; color: white;"
                                )
                                self.confirm_execute_button.clicked.connect(
                                    lambda: self.execute_script(script, files))
                                if layout is not None:
                                    layout.addWidget(
                                        self.confirm_execute_button)

                                # 在创建生成文件按钮的地方
                                self.confirm_generate_button = QPushButton(
                                    f"生成文件: {file_path}")
                                self.confirm_generate_button.setFixedSize(
                                    220, 36)  # 稍宽一些以显示文件名
                                self.confirm_generate_button.setStyleSheet(
                                    "background-color: #FF9800; color: white;"
                                )
                                self.confirm_generate_button.clicked.connect(
                                    lambda: self.generate_file(file_path, content))

                                if layout is not None:
                                    layout.addWidget(
                                        self.confirm_generate_button)

                            elif function_name == "output_direct_result":
                                result = args_dict["result"]
                                self.output_area.append("\n直接输出结果:")
                                self.output_area.append(result)

                            elif function_name == "generate_file_content":
                                file_path = args_dict["file_path"]
                                content = args_dict["content"]

                                # 添加文件生成确认按钮
                                self.confirm_generate_button = QPushButton(
                                    f"生成文件: {file_path}")
                                self.confirm_generate_button.clicked.connect(
                                    lambda: self.generate_file(file_path, content))
                                if layout is not None:
                                    layout.addWidget(
                                        self.confirm_generate_button)

                                self.output_area.append(
                                    f"\n准备生成文件: {file_path}")
                                self.output_area.append(
                                    f"内容预览:\n{content[:500]}{'...' if len(content) > 500 else ''}")
                        except json.JSONDecodeError:
                            self.output_area.append("\n参数解析失败")
                        except KeyError as e:
                            self.output_area.append(f"\n缺少必要参数: {str(e)}")
                else:
                    self.output_area.append("\n未检测到工具调用")

            else:
                # 不支持 Function Calling 的模型 - 回退到普通模式
                self.output_area.append("\n使用普通模式...")
                QApplication.processEvents()

                # 流式调用AI
                stream = self.client.chat.completions.create(
                    model=model_id,
                    messages=[{"role": "user", "content": prompt}],
                    stream=True,
                    temperature=0.2,
                )

                full_response = ""
                self.output_area.append("AI响应:")

                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        content_chunk = chunk.choices[0].delta.content
                        full_response += content_chunk
                        self.output_area.moveCursor(QTextCursor.End)
                        self.output_area.insertPlainText(content_chunk)
                        QApplication.processEvents()

                # 尝试提取Python代码块
                code_match = re.search(
                    r'```python\n(.*?)\n```', full_response, re.DOTALL)
                if code_match:
                    script = code_match.group(1)
                    self.output_area.append("\n检测到脚本代码:")
                    self.output_area.append(script)

                    # 添加执行确认按钮
                    self.confirm_execute_button = QPushButton("执行脚本")
                    self.confirm_execute_button.setFixedSize(120, 36)  # 设置固定尺寸
                    self.confirm_execute_button.setStyleSheet(
                        "background-color: #4CAF50; color: white;"
                    )
                    self.confirm_execute_button.clicked.connect(
                        lambda: self.execute_script(script, files))

                    if layout is not None:
                        layout.addWidget(self.confirm_execute_button)

                    # 在创建生成文件按钮的地方
                    if file_path is not None:
                        self.confirm_generate_button = QPushButton(
                            f"生成文件: {file_path}")
                        self.confirm_generate_button.setFixedSize(
                            220, 36)  # 稍宽一些以显示文件名
                        self.confirm_generate_button.setStyleSheet(
                            "background-color: #FF9800; color: white;"
                        )
                        self.confirm_generate_button.clicked.connect(
                            lambda: self.generate_file(file_path, full_response))
                        if layout := self.layout():
                            layout.addWidget(self.confirm_generate_button)
                else:
                    self.output_area.append("\n未检测到可执行脚本")

            # 保存到历史
            self.save_to_history(command, files, full_response)

        except Exception as e:
            self.output_area.append(f"\n执行出错: {str(e)}")
            import traceback
            self.output_area.append(traceback.format_exc())

        finally:
            # 移除进度条
            if hasattr(self, 'progress_bar'):
                if layout := self.layout():
                    layout.removeWidget(self.progress_bar)
                self.progress_bar.deleteLater()
                del self.progress_bar

    def generate_file(self, file_path, content):
        """直接生成文件内容"""
        try:
            # 弹出确认对话框
            reply = QMessageBox.question(self, "确认生成文件",
                                         f"是否生成文件: {file_path}?",
                                         QMessageBox.Yes | QMessageBox.No)

            if reply == QMessageBox.Yes:
                # 确保目录存在
                os.makedirs(os.path.dirname(file_path), exist_ok=True)

                # 写入文件
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)

                self.output_area.append(f"\n文件已生成: {file_path}")
                self.output_area.append(f"大小: {len(content)} 字节")

                # 移除确认按钮
                if hasattr(self, 'confirm_generate_button'):
                    if layout := self.layout():
                        layout.removeWidget(self.confirm_generate_button)
                    self.confirm_generate_button.deleteLater()
                    del self.confirm_generate_button
        except Exception as e:
            self.output_area.append(f"\n文件生成失败: {str(e)}")

    def execute_script(self, script, files):
        """执行Python脚本（带确认）"""
        try:
            # 弹出确认对话框
            reply = QMessageBox.question(self, "确认执行",
                                         "是否执行生成的脚本？",
                                         QMessageBox.Yes | QMessageBox.No)

            if reply == QMessageBox.Yes:
                print("execute_script: script =", script)
                # 移除确认按钮
                if hasattr(self, 'confirm_execute_button'):
                    if layout := self.layout():
                        layout.removeWidget(self.confirm_execute_button)
                    self.confirm_execute_button.deleteLater()
                    del self.confirm_execute_button

                # 创建临时脚本文件
                with tempfile.NamedTemporaryFile(suffix='.py', delete=False, mode='w', encoding='utf-8') as tmp:
                    tmp.write(script)
                    script_path = tmp.name

                # 为每个文件执行脚本
                for file in files:
                    self.output_area.append(f"\n处理文件: {file}")
                    result = subprocess.run(
                        ['python', script_path, file],
                        capture_output=True,
                        text=True
                    )

                    if result.stdout:
                        self.output_area.append("输出: " + result.stdout)
                    if result.stderr:
                        self.output_area.append("错误: " + result.stderr)

                    # 检查输出文件
                    base, ext = os.path.splitext(file)
                    output_file = f"{base}_out{ext}"
                    if os.path.exists(output_file):
                        self.output_area.append(f"成功创建: {output_file}")
                    else:
                        self.output_area.append(f"未找到输出文件: {output_file}")

                # 删除临时脚本
                os.unlink(script_path)
            else:
                self.output_area.append("\n用户取消执行")
        except Exception as e:
            self.output_area.append(f"\n执行错误: {str(e)}")

    def build_prompt(self, command, files, support_fc: bool):
        if support_fc:
            prompt = f"""
接下来将会给你一个用户的需求，你可以选择使用 Python 脚本来解决，或者直接输出文本内容给用户。
如果你选择生成 Python 脚本，请通过指定的 Function Call 工具来执行。"""
        else:
            prompt = f"""
接下来将会给你一个用户的需求，你可以选择使用 Python 脚本来解决，或者直接输出文本内容给用户。
如果你选择生成 Python 脚本，请保证你的输出中仅包含一个 Python 代码块，用户将会执行这个代码。
代码块以外可以包括其他描述性地内容以帮助你输出，这些内容会被忽略"""

        prompt += f"""
Python 脚本遵循以下规则：
1. 只生成可独立运行的Python脚本
2. 使用标准库优先（如图像处理用Pillow，文本处理用内置函数）
3. 脚本必须包含：if __name__ == '__main__'
4. 如果需要输入文件，通过sys.argv获取参数，第一个参数是输入文件
5. 如果需要输出文件，结果保存为：原文件名_out.扩展名

用户指令：{command}"""

        if files:
            prompt += "\n\n处理文件列表:"
            for file in files:
                prompt += f"\n- {file}"

                # 如果是小文本文件，添加内容预览
                if os.path.getsize(file) < 10240:  # 小于10KB
                    mime = mimetypes.guess_type(file)[0]
                    if mime and 'text' in mime:
                        try:
                            with open(file, 'r', encoding='utf-8') as f:
                                content = f.read(500)  # 只读取前500个字符
                                prompt += f"\n  文件内容预览:\n  {content}\n"
                        except Exception:
                            pass

        prompt += "\n\n输出格式：```python\n[代码]\n```"

        return prompt

    def save_to_history(self, command, files, script):
        entry = {
            "timestamp": int(time.time()),
            "command": command,
            "files": files,
            "script": script
        }
        self.history.append(entry)

        # 只保留最近10条记录
        if len(self.history) > 10:
            self.history = self.history[-10:]

        self.save_history()

    def load_api_key(self):
        # 从配置文件加载API密钥
        config_path = os.path.expanduser("~/.smart_assistant/config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    return config.get('api_key', '')
            except:
                return ''
        return ''

    def load_history(self):
        history_path = os.path.expanduser("~/.smart_assistant/history.json")
        if os.path.exists(history_path):
            try:
                with open(history_path, 'r') as f:
                    self.history = json.load(f)
            except:
                self.history = []

    def save_history(self):
        history_path = os.path.expanduser("~/.smart_assistant/history.json")
        os.makedirs(os.path.dirname(history_path), exist_ok=True)
        with open(history_path, 'w') as f:
            json.dump(self.history, f)

    def show_history(self):
        # 简化实现 - 实际应用中应创建历史记录窗口
        history_text = "最近操作:\n"
        for idx, entry in enumerate(reversed(self.history)):
            history_text += f"\n{idx+1}. {entry['command']}\n"
            if entry['files']:
                history_text += f"   文件: {', '.join(entry['files'])}\n"

        QMessageBox.information(self, "历史记录", history_text)

    def quit_app(self):
        self.save_history()
        QApplication.quit()

    def closeEvent(self, a0: QCloseEvent | None):
        if a0 is None:
            return
        a0.ignore()
        self.hide()


# Linux DBus服务实现
if platform.system() == "Linux":  # type: ignore
    class HotkeyService(dbus.service.Object):  # type: ignore
        def __init__(self, bus, object_path, callback):  # type: ignore
            dbus.service.Object.__init__( # type: ignore
                self, bus, object_path)  # type: ignore
            self.callback = callback  # type: ignore

        @dbus.service.method('com.example.Hotkeys',  # type: ignore
                             in_signature='', out_signature='')  # type: ignore
        def Activate(self):  # type: ignore
            self.callback()  # type: ignore


if __name__ == "__main__":
    # 创建应用实例
    app = QApplication(sys.argv)

    # 设置应用元数据
    app.setApplicationName("智能助手")
    app.setApplicationDisplayName("智能助手")
    app.setOrganizationName("DeepSeek")
    app.setOrganizationDomain("deepseek.com")

    # Windows特定设置
    set_windows_app_id()

    # 创建主窗口
    window = SmartAssistant()

    # 设置窗口图标
    icon_path = window.get_icon_path(ICON_PATH)
    if os.path.exists(icon_path):
        window.setWindowIcon(QIcon(icon_path))
    else:
        temp_icon = create_default_icon()
        if temp_icon:
            window.setWindowIcon(QIcon(temp_icon))

    # 设置窗口标题
    window.setWindowTitle("智能助手")

    # 启动应用
    sys.exit(app.exec_())
