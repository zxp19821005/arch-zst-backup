#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView, QApplication
)
from PySide6.QtCore import Qt, QTimer, Signal, QObject
from src.modules.logger import log
from modules.config_manager import config_manager

# 预定义的列配置常量
COLUMN_CONFIGS = {
    "backup_manager": {
        "pkgname": {
            "display_name": "pkgname",
            "type": "str",
            "width": 150,
            "resize_mode": "Stretch"
        },
        "epoch": {
            "display_name": "epoch",
            "type": "str",
            "width": 50,
            "resize_mode": "Fixed"
        },
        "pkgver": {
            "display_name": "pkgver",
            "type": "str",
            "width": 50,
            "resize_mode": "Stretch"
        },
        "relver": {
            "display_name": "relver",
            "type": "str",
            "width": 50,
            "resize_mode": "Fixed"
        },
        "arch": {
            "display_name": "arch",
            "type": "str",
            "width": 80,
            "resize_mode": "Fixed"
        },
        "location": {
            "display_name": "location",
            "type": "path",
            "width": 300,
            "resize_mode": "Stretch"
        }
    },
    "cache_manager": {
        "pkgname": {
            "display_name": "pkgname",
            "type": "str",
            "width": 150,
            "resize_mode": "Stretch"
        },
        "epoch": {
            "display_name": "epoch",
            "type": "str",
            "width": 80,
            "resize_mode": "Fixed"
        },
        "pkgver": {
            "display_name": "pkgver",
            "type": "str",
            "width": 150,
            "resize_mode": "Stretch"
        },
        "relver": {
            "display_name": "relver",
            "type": "str",
            "width": 80,
            "resize_mode": "Fixed"
        },
        "arch": {
            "display_name": "arch",
            "type": "str",
            "width": 80,
            "resize_mode": "Fixed"
        },
        "location": {
            "display_name": "location",
            "type": "str",
            "width": 300,
            "resize_mode": "Stretch"
        }
    }
}

class ListDisplayManager(QObject):
    """增强的列表显示管理器"""

    # 定义信号
    selection_changed = Signal(list)  # 选择变化信号
    data_filtered = Signal(int)       # 数据过滤信号

    def __init__(self, table_widget: QTableWidget, column_config: dict):
        """
        初始化表格显示管理器
        :param table_widget: 需要管理的表格控件
        :param column_config: 列配置字典，包含列名、显示名称、对齐方式等
        """
        super().__init__()
        self.table = table_widget
        self.column_config = column_config
        self.visible_columns = list(column_config.keys())
        self.data_cache = []
        self.filtered_data = []

        # 搜索定时器，用于延迟搜索
        self.search_timer = QTimer()
        self.search_timer.timeout.connect(self._apply_filter)
        self.search_timer.setSingleShot(True)

        self.setup_table()

    def setup_table(self):
        """初始化表格设置"""
        # 从配置加载显示设置
        config = config_manager.load_config()
        self.display_settings = config.get('displaySettings', {})

        # 设置表格列数
        self.table.setColumnCount(len(self.visible_columns))

        # 初始化表头项并立即设置对齐方式
        headers = [self.column_config[col].get('display_name', col)
                   for col in self.visible_columns]

        # 调试日志：输出字段名匹配情况
        for col_key, col_config in self.column_config.items():
            log.debug(f"字段名匹配: col_key={col_key}, display_name={col_config.get('display_name', '未设置')}")

        # 先创建所有表头项
        self.table.setColumnCount(len(headers))
        for col, text in enumerate(headers):
            item = QTableWidgetItem(text)
            # 表头统一居中显示
            item.setTextAlignment(Qt.AlignCenter)
            self.table.setHorizontalHeaderItem(col, item)

        # 设置表格基础属性
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.verticalHeader().setVisible(False)

        # 配置列宽和调整模式
        header = self.table.horizontalHeader()

        # 强制应用表头样式
        for i, col_key in enumerate(self.visible_columns, start=0):
            col_config = self.column_config[col_key]

            # 使用列配置中的resize_mode设置
            resize_mode = col_config.get('resize_mode', 'ResizeToContents')
            if resize_mode == 'Fixed':
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Fixed)
                # 使用列配置中的width设置
                width = col_config.get('width', 100)
                header.resizeSection(i, width)
            elif resize_mode == 'Stretch':
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
            else:  # 默认为ResizeToContents
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)

            alignment = self._get_column_alignment(col_key)

            # 表头统一居中显示，不受内容对齐方式影响
            self.table.horizontalHeaderItem(i).setTextAlignment(Qt.AlignCenter)

        # 强制刷新表头样式
        header.style().unpolish(header)
        header.style().polish(header)
        header.repaint()
        header.viewport().repaint()

        # 连接信号
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        self.table.cellDoubleClicked.connect(self._on_cell_double_clicked)

        # 初始化后立即强制应用样式
        self.table.style().unpolish(self.table)
        self.table.style().polish(self.table)
        self.table.repaint()

        # 强制刷新表格
        self.table.viewport().update()
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()
        self.table.updateGeometry()

        log.info("增强表格显示管理器初始化完成")

    def update_table(self, packages: list):
        """更新表格内容"""
        # 缓存数据
        self.data_cache = packages
        self.filtered_data = packages.copy()

        # 保存当前选择状态
        selected_items = self.get_selected_packages(self.data_cache)

        # 更新表格
        self._update_table_display(self.filtered_data)

        # 恢复选择状态
        self._restore_selection(selected_items)

        log.info(f"表格数据更新完成，共 {len(packages)} 行")

    def _update_table_display(self, data: list):
        """更新表格显示"""
        self.table.setRowCount(len(data))

        for row, pkg in enumerate(data):
            # 数据列
            for col, col_key in enumerate(self.visible_columns, start=0):
                # 直接获取值
                value = pkg.get(col_key, '')
                log.debug(f"列 '{col_key}' 的值: '{value}', 数据源字段: {list(pkg.keys())}")
                col_config = self.column_config[col_key]

                # 格式化数据（已经在cache_manager_operations.py中处理）
                # 特别处理epoch字段，当值为0或不存在时不显示
                if col_key == 'epoch' and (not value or str(value) == '0'):
                    formatted_value = ''
                else:
                    formatted_value = str(value) if value else ''

                item = QTableWidgetItem(formatted_value)

                # 设置对齐方式
                alignment = self._get_column_alignment(col_key)

                # 应用对齐方式
                if alignment == "center":
                    item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
                elif alignment == "right":
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                else:
                    item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                # 设置只读
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

                # 设置工具提示
                tooltip = col_config.get('tooltip')
                if tooltip:
                    item.setToolTip(tooltip)

                self.table.setItem(row, col, item)

    def _get_column_alignment(self, col_key):
        """获取列对齐方式
        
        Args:
            col_key: 列键名
            
        Returns:
            str: 对齐方式 ("left", "center", "right")
        """
        # 默认左对齐
        alignment = "left"

        # 字段名映射，处理新旧字段名的兼容性
        field_mapping = {
            'pkgname': 'name',
            'pkgver': 'version',
            'relver': 'pkgrel'
        }
        
        # 从配置中获取对齐方式
        # 配置文件结构: displaySettings.alignment.{英文列名}
        if 'alignment' in self.display_settings:
            # 首先尝试使用原始列名
            if col_key in self.display_settings['alignment']:
                alignment_value = self.display_settings['alignment'][col_key]
                # 检查值是字符串还是字典
                if isinstance(alignment_value, str):
                    alignment = alignment_value
                elif isinstance(alignment_value, dict) and 'alignment' in alignment_value:
                    alignment = alignment_value['alignment']
            # 如果没有找到，尝试使用旧的列名
            elif col_key in field_mapping and field_mapping[col_key] in self.display_settings['alignment']:
                alignment_value = self.display_settings['alignment'][field_mapping[col_key]]
                # 检查值是字符串还是字典
                if isinstance(alignment_value, str):
                    alignment = alignment_value
                elif isinstance(alignment_value, dict) and 'alignment' in alignment_value:
                    alignment = alignment_value['alignment']
        
        return alignment

    def filter_data(self, search_text='', filters=None):
        """过滤数据"""
        self.search_text = search_text
        self.filters = filters or {}

        # 延迟应用过滤器，避免频繁更新
        self.search_timer.start(300)  # 300ms延迟

    def _apply_filter(self):
        """应用过滤器"""
        filtered_data = []

        for item in self.data_cache:
            if self._match_filters(item):
                filtered_data.append(item)

        self.filtered_data = filtered_data
        self._update_table_display(self.filtered_data)

        # 发送过滤信号
        self.data_filtered.emit(len(self.filtered_data))

    def _match_filters(self, item):
        """检查项目是否匹配过滤条件"""
        # 文本搜索
        if hasattr(self, 'search_text') and self.search_text:
            found = False
            for col_key in self.visible_columns:
                value = str(item.get(col_key, '')).lower()
                if self.search_text.lower() in value:
                    found = True
                    break
            if not found:
                return False

        # 其他过滤条件
        if hasattr(self, 'filters'):
            for filter_key, filter_value in self.filters.items():
                if filter_value and item.get(filter_key) != filter_value:
                    return False

        return True

    # toggle_select_all方法已删除，因为不再有复选框列

    def get_selected_packages(self, packages: list = None) -> list:
        """获取选中的软件包"""
        if packages is None:
            packages = self.filtered_data

        selected = []
        selected_rows = self.table.selectionModel().selectedRows()
        
        # 获取表格中显示的数据
        table_data = []
        for row in range(self.table.rowCount()):
            pkgname_item = self.table.item(row, 0)  # 假设第一列是包名
            if pkgname_item:
                pkgname = pkgname_item.text()
                # 在原始数据中查找对应的软件包
                for pkg in packages:
                    if pkg.get("pkgname") == pkgname:
                        table_data.append(pkg)
                        break
        
        # 根据选中的行获取软件包
        for row_index in selected_rows:
            row = row_index.row()
            if row < len(table_data):
                selected.append(table_data[row])
        return selected

    def _restore_selection(self, selected_items):
        """恢复选择状态"""
        if not selected_items:
            return

        # 根据包名恢复选择
        selected_names = {item.get('pkgname') for item in selected_items}

        for row in range(self.table.rowCount()):
            if row < len(self.filtered_data):
                pkg_name = self.filtered_data[row].get('pkgname')
                if pkg_name in selected_names:
                    self.table.selectRow(row)

    def _on_selection_changed(self):
        """选择变化处理"""
        selected = self.get_selected_packages()
        self.selection_changed.emit(selected)
        
    def _on_cell_double_clicked(self, row, column):
        """双击单元格处理，复制单元格内容到剪贴板
        
        Args:
            row (int): 行索引
            column (int): 列索引
        """
        try:
            item = self.table.item(row, column)
            if item and item.text():
                # 获取单元格文本
                text = item.text()
                # 复制到剪贴板
                clipboard = QApplication.clipboard()
                clipboard.setText(text)
                log.info(f"已复制单元格内容到剪贴板: {text}")
        except Exception as e:
            log.error(f"复制单元格内容失败: {str(e)}")

    def set_column_visibility(self, column_key, visible):
        """设置列可见性"""
        if visible and column_key not in self.visible_columns:
            self.visible_columns.append(column_key)
        elif not visible and column_key in self.visible_columns:
            self.visible_columns.remove(column_key)

        # 重新设置表格
        self.setup_table()
        self.update_table(self.data_cache)

    def get_visible_columns(self):
        """获取可见列"""
        return self.visible_columns.copy()