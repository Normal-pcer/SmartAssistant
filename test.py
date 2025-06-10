import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QLineEdit, 
                             QHBoxLayout, QVBoxLayout, QGroupBox, 
                             QFormLayout, QPushButton, QFrame)
from PyQt5.QtCore import Qt

class MultiGroupWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        # 设置窗口标题和大小
        self.setWindowTitle('多组件组合示例')
        self.setGeometry(300, 300, 500, 350)
        
        # 创建主布局 - 垂直排列所有分组
        main_layout = QVBoxLayout()
        
        # ===== 分组1：使用水平布局 =====
        group1_label = QLabel("<b>水平布局分组</b>")
        group1_label.setAlignment(Qt.AlignCenter)
        
        # 创建水平布局的组件组合
        hbox1 = QHBoxLayout()
        hbox1.addWidget(QLabel('姓名:'))
        hbox1.addWidget(QLineEdit())
        hbox1.addWidget(QLabel('年龄:'))
        age_edit = QLineEdit()
        age_edit.setMaximumWidth(50)  # 限制宽度
        hbox1.addWidget(age_edit)
        
        # ===== 分组2：使用表单布局 =====
        group2_label = QLabel("<b>表单布局分组</b>")
        group2_label.setAlignment(Qt.AlignCenter)
        
        # 创建表单布局的组件组合
        form_layout = QFormLayout()
        form_layout.addRow('电子邮箱:', QLineEdit())
        form_layout.addRow('电话号码:', QLineEdit())
        
        # ===== 分组3：使用分组框容器 =====
        group_box = QGroupBox("分组框容器")
        vbox = QVBoxLayout()
        vbox.addWidget(QLabel('地址:'))
        vbox.addWidget(QLineEdit())
        vbox.addWidget(QLabel('城市:'))
        vbox.addWidget(QLineEdit())
        group_box.setLayout(vbox)
        
        # ===== 分组4：带分隔线的组合 =====
        group4_label = QLabel("<b>分隔线分组</b>")
        group4_label.setAlignment(Qt.AlignCenter)
        
        hbox2 = QHBoxLayout()
        hbox2.addWidget(QLabel('用户名:'))
        hbox2.addWidget(QLineEdit())
        hbox2.addWidget(QLabel('密码:'))
        password_edit = QLineEdit()
        password_edit.setEchoMode(QLineEdit.Password)  # 密码输入模式
        hbox2.addWidget(password_edit)
        
        # 创建分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: #c0c0c0;")
        
        # ===== 提交按钮 =====
        submit_btn = QPushButton('提交信息')
        submit_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        
        # 将所有组件添加到主布局
        main_layout.addWidget(group1_label)
        main_layout.addLayout(hbox1)
        main_layout.addSpacing(20)  # 添加间距
        
        main_layout.addWidget(group2_label)
        main_layout.addLayout(form_layout)
        main_layout.addSpacing(20)
        
        main_layout.addWidget(group_box)
        main_layout.addSpacing(20)
        
        main_layout.addWidget(group4_label)
        main_layout.addLayout(hbox2)
        main_layout.addSpacing(15)
        
        main_layout.addWidget(separator)
        main_layout.addSpacing(15)
        
        main_layout.addWidget(submit_btn, alignment=Qt.AlignCenter)
        
        # 设置主布局
        self.setLayout(main_layout)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    # 设置应用程序样式
    app.setStyle('Fusion')
    window = MultiGroupWindow()
    window.show()
    sys.exit(app.exec_())