from PyQt5.QtWidgets import QTextEdit

class OutputArea(QTextEdit):
    """输出区域"""

    def __init__(self) -> None:
        super().__init__()
        self.setReadOnly(True)
        self.setStyleSheet("background-color: #f0f0f0;")
