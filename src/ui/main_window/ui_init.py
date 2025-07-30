# -*- coding: utf-8 -*-
"""UI初始化混入类"""

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTableWidget, QHeaderView, QCheckBox,
    QTabWidget, QWidget, QSplitter, QFrame
)
from PySide6.QtCore import Qt

class UIInitMixin:
    """UI初始化相关的方法混入类"""
    
    def setup_toolbar(self, parent_layout):
        """设置工具栏"""
        toolbar_layout = QHBoxLayout()
        parent_layout.addLayout(toolbar_layout)
        
        # 全选/取消全选按钮
        self.select_all_button = QPushButton("全选")
        self.select_all_button.setCheckable(True)
        self.select_all_button.clicked.connect(self.toggle_select_all)
        toolbar_layout.addWidget(self.select_all_button)
        
        # 刷新按钮
        self.refresh_button = QPushButton("刷新")
        self.refresh_button.clicked.connect(self.refresh_data)
        toolbar_layout.addWidget(self.refresh_button)
        
        # 搜索框
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("搜索软件包...")
        self.search_edit.textChanged.connect(self.filter_packages)
        toolbar_layout.addWidget(self.search_edit)
        
        # 弹性空间
        toolbar_layout.addStretch()
        
        return toolbar_layout
    
    def setup_status_bar(self):
        """设置状态栏"""
        status_bar = self.statusBar()
        
        # 状态标签
        self.status_label = QLabel("就绪")
        status_bar.addWidget(self.status_label)
        
        # 进度标签
        self.progress_label = QLabel("")
        status_bar.addPermanentWidget(self.progress_label)
        
        return status_bar
    
    def update_status(self, message, progress=None):
        """更新状态栏"""
        if hasattr(self, 'status_label'):
            self.status_label.setText(message)
        if progress is not None and hasattr(self, 'progress_label'):
            self.progress_label.setText(f"{progress}%")
    
    def apply_theme(self):
        """应用主题"""
        # 从配置读取主题设置
        config = self.config_manager.get_config()
        theme = config.get('ui', {}).get('theme', 'default')
        
        if theme == 'dark':
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #2b2b2b;
                    color: #ffffff;
                }
                QTableWidget {
                    background-color: #3c3c3c;
                    alternate-background-color: #4a4a4a;
                    selection-background-color: #0078d4;
                    gridline-color: #555555;
                }
                QTabWidget::pane {
                    border: 1px solid #555555;
                    background-color: #2b2b2b;
                }
                QTabBar::tab {
                    background-color: #404040;
                    color: #ffffff;
                    padding: 8px 16px;
                    margin-right: 2px;
                    border: 1px solid #555555;
                }
                QTabBar::tab:selected {
                    background-color: #0078d4;
                }
                QPushButton {
                    background-color: #404040;
                    color: #ffffff;
                    border: 1px solid #555555;
                    padding: 6px 12px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #505050;
                }
                QPushButton:pressed {
                    background-color: #0078d4;
                }
                QLineEdit {
                    background-color: #3c3c3c;
                    color: #ffffff;
                    border: 1px solid #555555;
                    padding: 4px;
                    border-radius: 4px;
                }
                QLabel {
                    color: #ffffff;
                }
                QStatusBar {
                    background-color: #333333;
                    color: #ffffff;
                }
            """)
        else:
            # 默认主题或清除样式
            self.setStyleSheet("")
