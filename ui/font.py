from PyQt5.QtGui import QFont


class DefaultFont(QFont):
    """默认字体"""

    def __init__(self):
        super().__init__()
        self.setFamilies([
            "BlinkMacSystemFont",
            "Helvetica Neue",
            "PingFang SC",
            "Noto Sans",
            "Noto Sans SC",
            "Source Sans Pro",
            "Source Han Sans",
            "Segoe UI",
            "Arial",
            "Microsoft YaHei",
            "WenQuanYi Micro Hei",
            "sans-serif"
        ])
