"""
Windows 平台相关的特定设置
"""
import platform

WINDOWS = "Windows"

def is_windows() -> bool:
    return platform.system() == WINDOWS

def set_app_id(app_id: str) -> None:
    """设置应用 ID"""

    if not is_windows():
        return
    
    from ctypes import windll
    windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)