from typing import List
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QComboBox

TIP_TEXT = "模型："

class ModelSelector(QHBoxLayout):
    """模型选择框"""

    label: QLabel
    combo_box: QComboBox

    def __init__(self) -> None:
        super().__init__()
        self.setContentsMargins(0, 0, 0, 0)

        self.label = QLabel(TIP_TEXT)
        self.addWidget(self.label)
        self.combo_box = QComboBox()
        self.combo_box.setMinimumWidth(200)
        self.combo_box.setStyleSheet("QComboBox {padding: 4px;}")
        self.addWidget(self.combo_box)

        self.addStretch()
    
    def update_model_list(self, model_list: List[str]) -> None:
        """更新模型列表"""
        self.combo_box.clear()
        self.combo_box.addItems(model_list)
    
    def get_selected_index(self) -> int:
        """获取当前选中的模型索引"""
        return self.combo_box.currentIndex()
