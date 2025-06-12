from typing import List, Optional, Any
from PyQt5.QtWidgets import (
    QHBoxLayout, QVBoxLayout, QLabel, QComboBox, QPushButton, QDialog, QWidget, QTableWidget, QHeaderView, QTableWidgetItem, QLineEdit)
from PyQt5.QtCore import Qt
from core.assistant import Assistant
from core.ai_client import AIModel
from utils.general import log


class ModelSelector(QHBoxLayout):
    """模型选择框"""
    assistant: Assistant  # 连接主逻辑模块以获取信息

    label: QLabel
    combo_box: QComboBox
    config_button: QPushButton
    parent_widget: QWidget

    model_table: Optional[QTableWidget]

    def __init__(self, parent: QWidget, assistant: Assistant) -> None:
        super().__init__()
        self.setContentsMargins(0, 0, 0, 0)

        self.assistant = assistant

        self.label = QLabel("模型：")
        self.addWidget(self.label)
        self.combo_box = QComboBox()
        self.combo_box.setMinimumWidth(200)
        self.addWidget(self.combo_box)

        self.addStretch()

        self.config_button = QPushButton("配置")
        self.config_button.clicked.connect(self.open_config_dialog)
        self.addWidget(self.config_button)

        self.parent_widget = parent

    def update_model_list(self, model_list: List[str]) -> None:
        """更新模型列表"""
        self.combo_box.clear()
        self.combo_box.addItems(model_list)

    def get_selected_index(self) -> int:
        """获取当前选中的模型索引"""
        return self.combo_box.currentIndex()

    def open_config_dialog(self) -> None:
        """打开配置对话框"""
        dialog = QDialog(self.parent_widget)
        dialog.setWindowTitle("模型配置")
        dialog.setMinimumSize(700, 500)

        layout = QVBoxLayout()

        # 添加表格
        model_table = QTableWidget()
        model_table.setColumnCount(6)
        model_table.setHorizontalHeaderLabels(
            ["名称", "模型 ID", "API 地址", "API 密钥", "Function Call", "操作"])
        header = model_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # 名称列自适应
        header.setSectionResizeMode(
            1, QHeaderView.ResizeToContents)  # 模型ID固定宽度
        header.setSectionResizeMode(2, QHeaderView.Stretch)  # API地址自适应
        header.setSectionResizeMode(3, QHeaderView.Stretch)  # API密钥自适应
        header.setSectionResizeMode(
            4, QHeaderView.ResizeToContents)  # 功能支持固定宽度

        self.load_model_info_to_table(model_table)
        layout.addWidget(model_table)

        # 按钮区域
        button_layout = QHBoxLayout()

        add_button = QPushButton("添加模型")
        add_button.setFixedSize(100, 30)
        add_button.clicked.connect(lambda: self.add_model_row(model_table))
        button_layout.addWidget(add_button)

        save_button = QPushButton("保存")
        save_button.setFixedSize(80, 30)
        save_button.clicked.connect(
            lambda: (self.save_model_config(model_table), dialog.close()))
        button_layout.addWidget(save_button)

        cancel_button = QPushButton("取消")
        cancel_button.setFixedSize(80, 30)
        cancel_button.clicked.connect(
            lambda: (self.recall_modification(model_table), dialog.reject()))
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)
        dialog.setLayout(layout)
        dialog.setStyleSheet("""
            QPushButton{
                background-color: #4CAF50;
                color: white;
            }""")
        dialog.exec_()


    def delete_model_row(self, table: QTableWidget, index: int) -> None:
        """删除模型"""
        table.removeRow(index)
        self.assistant.get_models().pop(index)

    def add_model_row(self, table: QTableWidget, model: Optional[AIModel] = None) -> None:
        """添加模型"""
        model = model or AIModel("", "", "", "", False)
        index = table.rowCount()
        table.insertRow(index)

        # 名称，模型 ID，API 地址
        for col, val in enumerate([model.name, model.model_id, model.api_base]):
            table.setItem(index, col, QTableWidgetItem(val))

        api_key_edit = QLineEdit(model.api_key)
        api_key_edit.setEchoMode(QLineEdit.Password)
        table.setCellWidget(index, 3, api_key_edit)

        fc_item = QTableWidgetItem()
        fc_item.setFlags(Qt.ItemFlag(
            Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled))
        fc_item.setCheckState(
            Qt.CheckState.Checked if model.supports_functions else Qt.CheckState.Unchecked)
        table.setItem(index, 4, fc_item)

        del_button = QPushButton("删除")
        del_button.clicked.connect(lambda: self.delete_model_row(table, index))
        table.setCellWidget(index, 5, del_button)

        table.scrollToBottom()

    def recall_modification(self, table: QTableWidget) -> None:
        """撤销现有的修改"""
        self.assistant.config.load()
        self.load_model_info_to_table(table)

    def clear_table(self, table: QTableWidget) -> None:
        table.setRowCount(0)
        table.setColumnCount(6)

    def load_model_info_to_table(self, table: QTableWidget) -> None:
        models = self.assistant.get_models()
        self.clear_table(table)
        for model in models:
            self.add_model_row(table, model)

    def save_model_config(self, table: QTableWidget) -> None:
        config = self.assistant.config
        config.models.clear()

        for row in range(table.rowCount()):
            api_key_widget: Any = table.cellWidget(
                row, 3)  # 类型推导有误

            if not isinstance(api_key_widget, QLineEdit):
                log.error("save_model_config: 模型配置错误")
                raise RuntimeError("错误的表格数据")

            if item := table.item(row, 4):
                supports_fc = item.checkState() == Qt.Checked
            else:
                supports_fc = False

            api_key = api_key_widget.text()

            def get_text(item: Optional[QTableWidgetItem]) -> str:
                if item is None:
                    log.error("save_model_config: 模型配置错误")
                    raise RuntimeError("错误的表格数据")
                return item.text()

            model = AIModel(
                name=get_text(table.item(row, 0)),
                model_id=get_text(table.item(row, 1)),
                api_base=get_text(table.item(row, 2)),
                api_key=api_key,
                supports_functions=supports_fc
            )
            config.models.append(model)

        config.save()
