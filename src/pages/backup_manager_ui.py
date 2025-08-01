#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
备份管理器UI组件

该文件负责备份管理器页面的UI布局和组件初始化。
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton
)
from ui.components.button_style import ButtonStyle
from ui.components.search_box import FilterBox
from PySide6.QtWidgets import QTableWidget


class BackupManagerUI:
    """备份管理器UI类，负责处理所有UI相关操作"""

    def __init__(self, parent):
        """初始化UI

        Args:
            parent: 父级BackupManagerPage实例
        """
        self.parent = parent
        self.setup_ui()

    def setup_ui(self):
        """设置页面UI"""
        main_layout = QVBoxLayout()

        # 按钮栏
        button_layout = QHBoxLayout()

        # 添加过滤框
        self.filter_box = FilterBox()
        self.filter_box.filter_signal.connect(self.parent.handle_filter)
        self.filter_box.setMaximumWidth(300)  # 限制过滤框宽度
        button_layout.addWidget(self.filter_box)

        # 按钮布局
        button_layout.addStretch()  # 将按钮推到右侧

        # 刷新按钮
        self.scan_button = QPushButton("刷新")
        ButtonStyle.apply_primary_style(self.scan_button)
        button_layout.addWidget(self.scan_button)

        # 去重按钮
        self.dedupe_button = QPushButton("去重")
        ButtonStyle.apply_success_style(self.dedupe_button)
        button_layout.addWidget(self.dedupe_button)

        # 删除按钮
        self.delete_button = QPushButton("删除")
        ButtonStyle.apply_danger_style(self.delete_button)
        button_layout.addWidget(self.delete_button)
        main_layout.addLayout(button_layout)

        # 软件包表格
        self.table_widget = QTableWidget()
        self.table_widget.horizontalHeader().setStretchLastSection(True)
        main_layout.addWidget(self.table_widget)
        self.table_widget.setVisible(True)  # 显式设置表格可见

        self.parent.setLayout(main_layout)
