#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QCheckBox,
    QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QLabel
)
from PySide6.QtCore import Qt, QTimer, Signal, QObject
from modules.logger import log
from modules.config_manager import config_manager

# 预定义的列配置常量
COLUMN_CONFIGS = {
    "backup_manager": {
        "name": {
            "display_name": "名称",
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
        "version": {
            "display_name": "版本",
            "type": "str",
            "width": 50,
            "resize_mode": "Stretch"
        },
        "pkgrel": {
            "display_name": "发布号",
            "type": "str",
            "width": 50,
            "resize_mode": "Fixed"
        },
        "arch": {
            "display_name": "架构",
            "type": "str",
            "width": 80,
            "resize_mode": "Fixed"
        },
        "location": {
            "display_name": "位置",
            "type": "path",
            "width": 300,
            "resize_mode": "Stretch"
        }
    },
    "cache_manager": {
        "name": {
            "display_name": "名称",
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
        "version": {
            "display_name": "版本",
            "type": "str",
            "width": 150,
            "resize_mode": "Stretch"
        },
        "pkgrel": {
            "display_name": "发布号",
            "type": "str",
            "width": 80,
            "resize_mode": "Fixed"
        },
        "arch": {
            "display_name": "架构",
            "type": "str",
            "width": 80,
            "resize_mode": "Fixed"
        },
        "location": {
            "display_name": "位置",
            "type": "str",
            "width": 300,
            "resize_mode": "Stretch"
        }
    }
}

class TableDisplayManager(QObject):
    """增强的表格显示管理器"""

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

        # 设置表格列数（包含选择列）
        self.table.setColumnCount(len(self.visible_columns) + 1)

        # 初始化表头项并立即设置对齐方式
        headers = ["选择"] + [self.column_config[col].get('display_name', col)
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
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(0, 20)

        # 强制应用表头样式
        for i, col_key in enumerate(self.visible_columns, start=1):
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

            col_key_capitalized = col_key.capitalize() if col_key != 'pkgrel' else 'release'
            alignment = self.display_settings.get(col_key, {}).get("alignment", "left") if col_key in self.display_settings else self.display_settings.get(col_key_capitalized, {}).get("alignment", "left")

            # 表头统一居中显示，不受内容对齐方式影响
            self.table.horizontalHeaderItem(i).setTextAlignment(Qt.AlignCenter)

        # 强制刷新表头样式
        header.style().unpolish(header)
        header.style().polish(header)
        header.repaint()
        header.viewport().repaint()

        # 连接信号
        self.table.itemSelectionChanged.connect(self._on_selection_changed)

        # 初始化后立即强制应用样式
        self.table.style().unpolish(self.table)
        self.table.style().polish(self.table)
        self.table.repaint()

        # 强制应用表头对齐方式
        for i, col_key in enumerate(self.visible_columns, start=1):
            # 表头统一居中显示，不受内容对齐方式影响
            header_item = self.table.horizontalHeaderItem(i)
            if header_item:
                header_item.setTextAlignment(Qt.AlignCenter)
                print(f"[DEBUG] 设置表头{i}对齐方式: center")

        # 强制刷新表格
        print("[DEBUG] 开始强制刷新表格视图")
        self.table.viewport().update()
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()
        print("[DEBUG] 表格刷新完成")

        # 额外同步机制
        self.table.style().unpolish(self.table)
        self.table.style().polish(self.table)
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
            # 选择复选框
            checkbox = QCheckBox()
            checkbox.setChecked(False)
            checkbox.stateChanged.connect(self._on_checkbox_changed)
            self.table.setCellWidget(row, 0, checkbox)

            # 数据列
            for col, col_key in enumerate(self.visible_columns, start=1):
                value = pkg.get(col_key.lower(), pkg.get(col_key.capitalize(), ''))
                log.debug(f"列 '{col_key}' 的值: '{value}', 数据源字段: {list(pkg.keys())}")
                col_config = self.column_config[col_key]

                # 格式化数据
                formatted_value = self._format_value(value, col_config)

                item = QTableWidgetItem(formatted_value)

                # 设置对齐方式
                alignment = "left"  # 默认左对齐

                # 从配置中获取对齐方式
                # 配置文件结构: displaySettings.alignment.{英文列名}
                if 'alignment' in self.display_settings:
                    # 首先尝试使用原始列名
                    if col_key in self.display_settings['alignment']:
                        alignment = self.display_settings['alignment'][col_key]
                    # 尝试使用首字母大写的列名（处理pkgrel特殊情况）
                    else:
                        col_key_capitalized = col_key.capitalize() if col_key != 'pkgrel' else 'release'
                        if col_key_capitalized in self.display_settings['alignment']:
                            alignment = self.display_settings['alignment'][col_key_capitalized]

                # 应用对齐方式
                if alignment == "center":
                    item.setTextAlignment(Qt.AlignCenter)
                elif alignment == "right":
                    item.setTextAlignment(Qt.AlignRight)
                else:
                    item.setTextAlignment(Qt.AlignLeft)
                # 设置只读
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

                # 设置工具提示
                tooltip = col_config.get('tooltip')
                if tooltip:
                    item.setToolTip(tooltip)

                self.table.setItem(row, col, item)

    def _format_value(self, value, col_config):
        """格式化值"""
        data_type = col_config.get('type', 'str')
        if data_type == 'path' and value:
            # 处理路径分隔符（兼容Windows和Linux）
            path = str(value).replace('\\', '/')  # 统一替换为Linux风格分隔符
            formatted_value = path.split('/')[-1]  # 提取最后一级目录
            log.debug(f"格式化路径: 原始值='{value}', 格式化后='{formatted_value}'")
            return formatted_value
        return str(value) if value else ''

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

    def toggle_select_all(self, state):
        """全选/取消全选"""
        is_checked = state == Qt.CheckState.Checked
        for row in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(row, 0)
            if checkbox:
                checkbox.setChecked(is_checked)

        action = "全选" if is_checked else "取消全选"
        log.info(f"{action}所有显示的软件包")

    def get_selected_packages(self, packages: list = None) -> list:
        """获取选中的软件包"""
        if packages is None:
            packages = self.filtered_data

        selected = []
        for row in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked() and row < len(packages):
                selected.append(packages[row])
        return selected

    def _restore_selection(self, selected_items):
        """恢复选择状态"""
        if not selected_items:
            return

        # 根据包名恢复选择
        selected_names = {item.get('name') for item in selected_items}

        for row in range(self.table.rowCount()):
            if row < len(self.filtered_data):
                pkg_name = self.filtered_data[row].get('name')
                if pkg_name in selected_names:
                    checkbox = self.table.cellWidget(row, 0)
                    if checkbox:
                        checkbox.setChecked(True)

    def _on_selection_changed(self):
        """选择变化处理"""
        selected = self.get_selected_packages()
        self.selection_changed.emit(selected)

    def _on_checkbox_changed(self):
        """复选框变化处理"""
        self._on_selection_changed()

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

    def export_data(self, file_path, selected_only=False):
        """导出数据"""
        import csv

        data_to_export = self.get_selected_packages() if selected_only else self.filtered_data

        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            if not data_to_export:
                return

            fieldnames = ['name'] + self.visible_columns
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            # 写入表头
            header = {field: self.column_config.get(field, {}).get('display_name', field)
                     for field in fieldnames}
            writer.writerow(header)

            # 写入数据
            for item in data_to_export:
                row_data = {field: item.get(field, '') for field in fieldnames}
                writer.writerow(row_data)

        log.info(f"数据导出完成: {file_path}, 共 {len(data_to_export)} 行")

# 保持向后兼容性
class ListDisplayManager(TableDisplayManager):
    """向后兼容的类名"""

    def __init__(self, table_widget: QTableWidget, column_options: list):
        # 将旧格式转换为新格式
        column_config = {}
        for i, col in enumerate(column_options):
            column_config[col] = {
                'display_name': col,
                'type': 'path' if 'path' in col.lower() or col == 'location' else 'str',
                'alignment': 'left',
                'width': 100
            }

        super().__init__(table_widget, column_config)#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QCheckBox,
    QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QLabel
)
from PySide6.QtCore import Qt, QTimer, Signal, QObject
from modules.logger import log
from modules.config_manager import config_manager

# 预定义的列配置常量
COLUMN_CONFIGS = {
    "backup_manager": {
        "name": {
            "display_name": "名称",
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
        "version": {
            "display_name": "版本",
            "type": "str",
            "width": 50,
            "resize_mode": "Stretch"
        },
        "pkgrel": {
            "display_name": "发布号",
            "type": "str",
            "width": 50,
            "resize_mode": "Fixed"
        },
        "arch": {
            "display_name": "架构",
            "type": "str",
            "width": 80,
            "resize_mode": "Fixed"
        },
        "location": {
            "display_name": "位置",
            "type": "path",
            "width": 300,
            "resize_mode": "Stretch"
        }
    },
    "cache_manager": {
        "name": {
            "display_name": "名称",
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
        "version": {
            "display_name": "版本",
            "type": "str",
            "width": 150,
            "resize_mode": "Stretch"
        },
        "pkgrel": {
            "display_name": "发布号",
            "type": "str",
            "width": 80,
            "resize_mode": "Fixed"
        },
        "arch": {
            "display_name": "架构",
            "type": "str",
            "width": 80,
            "resize_mode": "Fixed"
        },
        "location": {
            "display_name": "位置",
            "type": "str",
            "width": 300,
            "resize_mode": "Stretch"
        }
    }
}

class TableDisplayManager(QObject):
    """增强的表格显示管理器"""

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

        # 设置表格列数（包含选择列）
        self.table.setColumnCount(len(self.visible_columns) + 1)

        # 初始化表头项并立即设置对齐方式
        headers = ["选择"] + [self.column_config[col].get('display_name', col)
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
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(0, 20)

        # 强制应用表头样式
        for i, col_key in enumerate(self.visible_columns, start=1):
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

            col_key_capitalized = col_key.capitalize() if col_key != 'pkgrel' else 'release'
            alignment = self.display_settings.get(col_key, {}).get("alignment", "left") if col_key in self.display_settings else self.display_settings.get(col_key_capitalized, {}).get("alignment", "left")

            # 表头统一居中显示，不受内容对齐方式影响
            self.table.horizontalHeaderItem(i).setTextAlignment(Qt.AlignCenter)

        # 强制刷新表头样式
        header.style().unpolish(header)
        header.style().polish(header)
        header.repaint()
        header.viewport().repaint()

        # 连接信号
        self.table.itemSelectionChanged.connect(self._on_selection_changed)

        # 初始化后立即强制应用样式
        self.table.style().unpolish(self.table)
        self.table.style().polish(self.table)
        self.table.repaint()

        # 强制应用表头对齐方式
        for i, col_key in enumerate(self.visible_columns, start=1):
            # 表头统一居中显示，不受内容对齐方式影响
            header_item = self.table.horizontalHeaderItem(i)
            if header_item:
                header_item.setTextAlignment(Qt.AlignCenter)
                print(f"[DEBUG] 设置表头{i}对齐方式: center")

        # 强制刷新表格
        print("[DEBUG] 开始强制刷新表格视图")
        self.table.viewport().update()
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()
        print("[DEBUG] 表格刷新完成")

        # 额外同步机制
        self.table.style().unpolish(self.table)
        self.table.style().polish(self.table)
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
            # 选择复选框
            checkbox = QCheckBox()
            checkbox.setChecked(False)
            checkbox.stateChanged.connect(self._on_checkbox_changed)
            self.table.setCellWidget(row, 0, checkbox)

            # 数据列
            for col, col_key in enumerate(self.visible_columns, start=1):
                value = pkg.get(col_key.lower(), pkg.get(col_key.capitalize(), ''))
                log.debug(f"列 '{col_key}' 的值: '{value}', 数据源字段: {list(pkg.keys())}")
                col_config = self.column_config[col_key]

                # 格式化数据
                formatted_value = self._format_value(value, col_config)

                item = QTableWidgetItem(formatted_value)

                # 设置对齐方式
                alignment = "left"  # 默认左对齐

                # 从配置中获取对齐方式
                # 配置文件结构: displaySettings.alignment.{英文列名}
                if 'alignment' in self.display_settings:
                    # 首先尝试使用原始列名
                    if col_key in self.display_settings['alignment']:
                        alignment = self.display_settings['alignment'][col_key]
                    # 尝试使用首字母大写的列名（处理pkgrel特殊情况）
                    else:
                        col_key_capitalized = col_key.capitalize() if col_key != 'pkgrel' else 'release'
                        if col_key_capitalized in self.display_settings['alignment']:
                            alignment = self.display_settings['alignment'][col_key_capitalized]

                # 应用对齐方式
                if alignment == "center":
                    item.setTextAlignment(Qt.AlignCenter)
                elif alignment == "right":
                    item.setTextAlignment(Qt.AlignRight)
                else:
                    item.setTextAlignment(Qt.AlignLeft)
                # 设置只读
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

                # 设置工具提示
                tooltip = col_config.get('tooltip')
                if tooltip:
                    item.setToolTip(tooltip)

                self.table.setItem(row, col, item)

    def _format_value(self, value, col_config):
        """格式化值"""
        data_type = col_config.get('type', 'str')
        if data_type == 'path' and value:
            # 处理路径分隔符（兼容Windows和Linux）
            path = str(value).replace('\\', '/')  # 统一替换为Linux风格分隔符
            formatted_value = path.split('/')[-1]  # 提取最后一级目录
            log.debug(f"格式化路径: 原始值='{value}', 格式化后='{formatted_value}'")
            return formatted_value
        return str(value) if value else ''

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

    def toggle_select_all(self, state):
        """全选/取消全选"""
        is_checked = state == Qt.CheckState.Checked
        for row in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(row, 0)
            if checkbox:
                checkbox.setChecked(is_checked)

        action = "全选" if is_checked else "取消全选"
        log.info(f"{action}所有显示的软件包")

    def get_selected_packages(self, packages: list = None) -> list:
        """获取选中的软件包"""
        if packages is None:
            packages = self.filtered_data

        selected = []
        for row in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked() and row < len(packages):
                selected.append(packages[row])
        return selected

    def _restore_selection(self, selected_items):
        """恢复选择状态"""
        if not selected_items:
            return

        # 根据包名恢复选择
        selected_names = {item.get('name') for item in selected_items}

        for row in range(self.table.rowCount()):
            if row < len(self.filtered_data):
                pkg_name = self.filtered_data[row].get('name')
                if pkg_name in selected_names:
                    checkbox = self.table.cellWidget(row, 0)
                    if checkbox:
                        checkbox.setChecked(True)

    def _on_selection_changed(self):
        """选择变化处理"""
        selected = self.get_selected_packages()
        self.selection_changed.emit(selected)

    def _on_checkbox_changed(self):
        """复选框变化处理"""
        self._on_selection_changed()

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

    def export_data(self, file_path, selected_only=False):
        """导出数据"""
        import csv

        data_to_export = self.get_selected_packages() if selected_only else self.filtered_data

        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            if not data_to_export:
                return

            fieldnames = ['name'] + self.visible_columns
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            # 写入表头
            header = {field: self.column_config.get(field, {}).get('display_name', field)
                     for field in fieldnames}
            writer.writerow(header)

            # 写入数据
            for item in data_to_export:
                row_data = {field: item.get(field, '') for field in fieldnames}
                writer.writerow(row_data)

        log.info(f"数据导出完成: {file_path}, 共 {len(data_to_export)} 行")

# 保持向后兼容性
class ListDisplayManager(TableDisplayManager):
    """向后兼容的类名"""

    def __init__(self, table_widget: QTableWidget, column_options: list):
        # 将旧格式转换为新格式
        column_config = {}
        for i, col in enumerate(column_options):
            column_config[col] = {
                'display_name': col,
                'type': 'path' if 'path' in col.lower() or col == 'location' else 'str',
                'alignment': 'left',
                'width': 100
            }

        super().__init__(table_widget, column_config)                selected.append(packages[row])
        return selected

    def _restore_selection(self, selected_items):
        """恢复选择状态"""
        if not selected_items:
            return

        # 根据包名恢复选择
        selected_names = {item.get('name') for item in selected_items}

        for row in range(self.table.rowCount()):
            if row < len(self.filtered_data):
                pkg_name = self.filtered_data[row].get('name')
                if pkg_name in selected_names:
                    checkbox = self.table.cellWidget(row, 0)
                    if checkbox:
                        checkbox.setChecked(True)

    def _on_selection_changed(self):
        """选择变化处理"""
        selected = self.get_selected_packages()
        self.selection_changed.emit(selected)

    def _on_checkbox_changed(self):
        """复选框变化处理"""
        self._on_selection_changed()

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

    def export_data(self, file_path, selected_only=False):
        """导出数据"""
        import csv

        data_to_export = self.get_selected_packages() if selected_only else self.filtered_data

        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            if not data_to_export:
                return

            fieldnames = ['name'] + self.visible_columns
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            # 写入表头
            header = {field: self.column_config.get(field, {}).get('display_name', field)
                     for field in fieldnames}
            writer.writerow(header)

            # 写入数据
            for item in data_to_export:
                row_data = {field: item.get(field, '') for field in fieldnames}
                writer.writerow(row_data)

        log.info(f"数据导出完成: {file_path}, 共 {len(data_to_export)} 行")

# 保持向后兼容性
class ListDisplayManager(TableDisplayManager):
    """向后兼容的类名"""

    def __init__(self, table_widget: QTableWidget, column_options: list):
        # 将旧格式转换为新格式
        column_config = {}
        for i, col in enumerate(column_options):
            column_config[col] = {
                'display_name': col,
                'type': 'path' if 'path' in col.lower() or col == 'location' else 'str',
                'alignment': 'left',
                'width': 100
            }

        super().__init__(table_widget, column_config)