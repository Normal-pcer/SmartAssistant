STYLESHEET = """
    /* 主窗口样式 */
    QMainWindow {
        background-color: #f5f5f5;
    }
    
    /* 标签样式 */
    QLabel {
        font-weight: bold;
        color: #333;
    }
    
    /* 输入框样式 */
    QTextEdit, QListWidget, QComboBox, QLineEdit {
        background-color: white;
        border: 1px solid #ddd;
        border-radius: 4px;
        padding: 6px;
    }
    
    /* 按钮基础样式 */
    QPushButton {
        min-height: 32px;
        min-width: 80px;
        padding: 6px 12px;
        border-radius: 4px;
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
    }
    QProgressBar::chunk {
        background-color: #4CAF50;
    }
    
    /* 表格样式 */
    QTableWidget {
        background-color: white;
        border: 1px solid #ddd;
    }
    QHeaderView::section {
        background-color: #f0f0f0;
        padding: 6px;
        border: none;
    }
    
    /* 状态栏样式 */
    QStatusBar {
        background-color: #e0e0e0;
        color: #333;
        padding: 2px 8px;
    }
"""