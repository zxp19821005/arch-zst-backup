#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QCheckBox, QHeaderView,
    QMessageBox, QInputDialog, QLineEdit
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon
from ui.components.list_display_manager import ListDisplayManager
from ui.components.search_box import FilterBox
from ui.components.button_style import ButtonStyle
from PySide6.QtWidgets import QTableWidget
from modules.logger import log

class CacheManagerUI:
    """缓存管理器UI类，负责创建和管理UI元素"""

    def __init__(self, parent):
        """初始化UI

        Args:
            parent: 父级CacheManagerPage实例
        """
        self.parent = parent
        self.table_widget = None
        self.filter_box = None
        self.scan_button = None
        self.dedupe_button = None
        self.delete_button = None
        self.update_button = None
        self.clean_cache_button = None
        self.backup_newer_button = None
        self.backup_to_subdir_button = None
        self.setup_ui()

    def setup_ui(self):
        """设置页面UI"""
        main_layout = QVBoxLayout()
        # 操作按钮栏
        button_layout = QHBoxLayout()

        # 添加过滤框
        self.filter_box = FilterBox()
        self.filter_box.filter_signal.connect(self.parent.handle_filter)
        self.filter_box.setMaximumWidth(300)  # 限制过滤框宽度
        button_layout.addWidget(self.filter_box)

        # 按钮布局 - 靠右对齐
        button_layout.addStretch()

        # 创建所有按钮
        self._create_buttons(button_layout)

        main_layout.addLayout(button_layout)

        # 创建表格
        self._create_table(main_layout)

        # 设置页面布局
        self.parent.setLayout(main_layout)
        log.info("缓存软件管理页面UI设置完成")

    def _create_buttons(self, button_layout):
        """创建所有按钮

        Args:
            button_layout: 按钮布局
        """
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

        # 检查更新按钮
        self.update_button = QPushButton("检查更新")
        ButtonStyle.apply_primary_style(self.update_button)
        button_layout.addWidget(self.update_button)

        # 备份较新版本按钮
        self.backup_newer_button = QPushButton("备份较新版本")
        ButtonStyle.apply_success_style(self.backup_newer_button)
        button_layout.addWidget(self.backup_newer_button)

        # 备份到子目录按钮
        self.backup_to_subdir_button = QPushButton("备份到子目录")
        ButtonStyle.apply_secondary_style(self.backup_to_subdir_button)
        button_layout.addWidget(self.backup_to_subdir_button)

        # 缓存清理按钮
        self.clean_cache_button = QPushButton("缓存清理")
        ButtonStyle.apply_warning_style(self.clean_cache_button)
        button_layout.addWidget(self.clean_cache_button)

    def _create_table(self, main_layout):
        """创建表格组件

        Args:
            main_layout: 主布局
        """
        # 创建表格
        self.table_widget = QTableWidget()
        self.table_widget.horizontalHeader().setStretchLastSection(True)

        # 设置表格颜色
        table_palette = self.table_widget.palette()
        table_palette.setColor(self.table_widget.backgroundRole(), Qt.black)
        table_palette.setColor(self.table_widget.foregroundRole(), Qt.white)
        self.table_widget.setPalette(table_palette)

        # 使用预定义的列配置
        from ui.components.list_display_manager import COLUMN_CONFIGS
        column_config = COLUMN_CONFIGS["cache_manager"]
        column_names = list(column_config.keys())

        main_layout.addWidget(self.table_widget)
        self.parent.list_display_manager = ListDisplayManager(self.table_widget, column_config)

        # 注释掉设置文件路径列的代码，因为QTableWidget没有这个方法
        # location_index = column_names.index("location")
        # self.table_widget.set_path_column(location_index)

        # 注释掉信号连接，因为QTableWidget没有这些信号
        # self.table_widget.item_copied.connect(self.parent.on_item_copied)
        # self.table_widget.item_renamed.connect(self.parent.on_item_renamed)
        # self.table_widget.item_deleted.connect(self.parent.handle_context_menu_delete)

        # 应用 displaySettings 中的列对齐方式
        self.parent._apply_column_alignment = lambda config: None
