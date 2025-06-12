"""键盘相关实用工具"""
from PyQt5.QtCore import pyqtSignal, QObject
from pynput import keyboard
from time import sleep


class Hotkey(QObject):
    signal = pyqtSignal()

    def __init__(self, key: str):
        super().__init__()
        self.listener = keyboard.GlobalHotKeys({
            key: self.signal.emit})

    def listen(self) -> None:
        """开始监听"""
        self.listener.start()
        while True:
            sleep(1)  # 维持线程运行
