"""
通用工具函数
"""
from typing import TypeVar, TextIO, Optional
from time import time, localtime, strftime
from sys import stderr
from os.path import expanduser

Path = str
T = TypeVar('T', bound=object)
U = TypeVar('U')
LOG_FILE = expanduser("~/.smart_assistant/log.txt")

def set_default(source: Optional[T], default: U) -> T | U:
    """
    如同 Javascript 的 a ?? b 运算符
    """
    if source is None:
        return default
    else:
        return source

class Logger:
    """日志"""
    screen_file: TextIO
    enable_debug: bool = False
    disk_file_path: Optional[Path] = None

    def __init__(self, screen_file: TextIO = stderr, disk_file_path: Optional[Path] = None):
        self.screen_file = screen_file
        self.disk_file_path = disk_file_path

    @staticmethod
    def get_time_str() -> str:
        """获取当前时间字符串"""
        return strftime("%Y-%m-%d %H:%M:%S", localtime(time()))

    def info(self, message: str) -> None:
        """输出信息"""
        print(f"[INFO][{self.get_time_str()}] {message}", file=self.screen_file)
        if self.disk_file_path is not None:
            with open(self.disk_file_path, "w+", encoding="utf-8") as f:
                print(f"[INFO][{self.get_time_str()}] {message}", file=f)
    
    def warning(self, message: str) -> None:
        """输出警告"""
        print(f"[WARNING][{self.get_time_str()}] {message}", file=self.screen_file)
        if self.disk_file_path is not None:
            with open(self.disk_file_path, "w+", encoding="utf-8") as f:
                print(f"[WARNING][{self.get_time_str()}] {message}", file=f)
    
    def error(self, message: str) -> None:
        """输出错误"""
        print(f"[ERROR][{self.get_time_str()}] {message}", file=self.screen_file)
        if self.disk_file_path is not None:
            with open(self.disk_file_path, "w+", encoding="utf-8") as f:
                print(f"[ERROR][{self.get_time_str()}] {message}", file=f)
    
    def debug(self, message: str) -> None:
        """输出调试信息"""
        if not self.enable_debug:
            return
        print(f"[DEBUG][{self.get_time_str()}] {message}", file=self.screen_file)
        if self.disk_file_path is not None:
            with open(self.disk_file_path, "w+", encoding="utf-8") as f:
                print(f"[DEBUG][{self.get_time_str()}] {message}", file=f)

log = Logger(disk_file_path=LOG_FILE)
