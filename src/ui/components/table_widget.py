# -*- coding: utf-8 -*-
"""增强的表格组件"""

from PySide6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox,
    QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLineEdit,
    QLabel, QComboBox, QMenu, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QAction
from datetime import datetime

class TableWidget(QWidget):
    """增强的表格组件"""
    
    # 定义信号
    selection_changed = Signal(list)  # 选择变化信号
    data_filtered = Signal(int)       # 数据过滤信号
    action_requested = Signal(str, list)  # 操作请求信号
    
    def __init__(self, column_config, parent=None):
        """
        初始化表格组件
        :param column_config: 列配置字典
        :param parent: 父组件
        """
        super().__init__(parent)
        
        self.column_config = column_config
        self.data_cache = []
        self.filtered_data = []
        
        # 搜索定时器
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.perform_filter)
        
        self.init_ui()
        self.setup_table()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 工具栏
        toolbar = self.create_toolbar()
        layout.addWidget(toolbar)
        
        # 表格
        self.table = QTableWidget()
        layout.addWidget(self.table)
        
        # 状态栏
        status_bar = self.create_status_bar()
        layout.addWidget(status_bar)
    
    def create_toolbar(self):
        """创建工具栏"""
        toolbar = QWidget()
        layout = QHBoxLayout(toolbar)
        
        # 全选按钮
        self.select_all_btn = QPushButton("全选")
        self.select_all_btn.setCheckable(True)
        self.select_all_btn.clicked.connect(self.toggle_select_all)
        layout.addWidget(self.select_all_btn)
        
        # 搜索框
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("搜索...")
        self.search_edit.textChanged.connect(self.on_search_text_changed)
        layout.addWidget(self.search_edit)
        
        # 列显示控制
        self.column_combo = QComboBox()
        self.column_combo.addItem("显示所有列")
        for col_name in self.column_config.keys():
            self.column_combo.addItem(f"隐藏: {col_name}")
        self.column_combo.currentTextChanged.connect(self.on_column_visibility_changed)
        layout.addWidget(self.column_combo)
        
        # 刷新按钮
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self.refresh_data)
        layout.addWidget(refresh_btn)
        
        layout.addStretch()
        return toolbar
    
    def create_status_bar(self):
        """创建状态栏"""
        status_bar = QWidget()
        layout = QHBoxLayout(status_bar)
        
        self.info_label = QLabel("就绪")
        layout.addWidget(self.info_label)
        
        layout.addStretch()
        
        self.count_label = QLabel("0 项")
        layout.addWidget(self.count_label)
        
        return status_bar
    
    def setup_table(self):
        """设置表格"""
        columns = list(self.column_config.keys())
        self.table.setColumnCount(len(columns) + 1)  # +1 为选择列
        
        headers = ["选择"] + columns
        self.table.setHorizontalHeaderLabels(headers)
        
        # 设置表格属性
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        
        # 设置列宽
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(0, 50)
        
        for i, (col_name, config) in enumerate(self.column_config.items(), start=1):
            width = config.get('width', 100)
            if width:
                header.resizeSection(i, width)
            else:
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
        
        # 隐藏行号
        self.table.verticalHeader().setVisible(False)
        
        # 右键菜单
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        
        # 连接信号
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
    
    def update_data(self, data_list):
        """更新数据"""
        self.data_cache = data_list
        self.filtered_data = data_list.copy()
        self.refresh_table()
    
    def refresh_table(self):
        """刷新表格显示"""
        # 保存当前状态
        scroll_pos = self.table.verticalScrollBar().value()
        selected_items = self.get_selected_identifiers()
        
        # 清空表格
        self.table.setRowCount(0)
        
        # 填充数据
        self.table.setRowCount(len(self.filtered_data))
        
        for row, item_data in enumerate(self.filtered_data):
            # 选择框
            checkbox = QCheckBox()
            checkbox.stateChanged.connect(lambda state, r=row: self.on_checkbox_changed(r, state))
            self.table.setCellWidget(row, 0, checkbox)
            
            # 数据列
            for col, (col_name, config) in enumerate(self.column_config.items(), start=1):
                value = item_data.get(col_name, "")
                
                # 格式化数据
                formatted_value = self.format_value(value, config)
                
                item = QTableWidgetItem(str(formatted_value))
                
                # 设置对齐
                alignment = config.get('alignment', 'left')
                if alignment == 'center':
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                elif alignment == 'right':
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
                
                # 设置只读
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                
                # 工具提示
                tooltip = config.get('tooltip')
                if tooltip:
                    item.setToolTip(tooltip)
                
                self.table.setItem(row, col, item)
        
        # 恢复状态
        self.restore_selection(selected_items)
        self.table.verticalScrollBar().setValue(scroll_pos)
        
        # 更新状态
        self.update_status()
    
    def format_value(self, value, config):
        """格式化数值"""
        data_type = config.get('type', 'str')
        
        if data_type == 'datetime' and value:
            try:
                if isinstance(value, str):
                    dt = datetime.fromisoformat(value)
                else:
                    dt = value
                return dt.strftime(config.get('format', '%Y-%m-%d %H:%M:%S'))
            except:
                return str(value)
        elif data_type == 'size' and value:
            try:
                size = int(value)
                for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                    if size < 1024:
                        return f"{size:.1f} {unit}"
                    size /= 1024
                return f"{size:.1f} PB"
            except:
                return str(value)
        
        return value
    
    def on_search_text_changed(self, text):
        """搜索文本变化"""
        # 延迟搜索，避免频繁过滤
        self.search_timer.stop()
        self.search_timer.start(300)
    
    def perform_filter(self):
        """执行过滤"""
        search_text = self.search_edit.text().lower()
        
        if not search_text:
            self.filtered_data = self.data_cache.copy()
        else:
            self.filtered_data = []
            for item in self.data_cache:
                # 搜索所有列
                found = False
                for col_name in self.column_config.keys():
                    value = str(item.get(col_name, "")).lower()
                    if search_text in value:
                        found = True
                        break
                
                if found:
                    self.filtered_data.append(item)
        
        self.refresh_table()
        self.data_filtered.emit(len(self.filtered_data))
    
    def toggle_select_all(self):
        """切换全选"""
        is_checked = self.select_all_btn.isChecked()
        
        for row in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(row, 0)
            if checkbox:
                checkbox.setChecked(is_checked)
        
        text = "取消全选" if is_checked else "全选"
        self.select_all_btn.setText(text)
    
    def get_selected_rows(self):
        """获取选中的行"""
        selected_rows = []
        for row in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                selected_rows.append(row)
        return selected_rows
    
    def get_selected_data(self):
        """获取选中的数据"""
        selected_data = []
        selected_rows = self.get_selected_rows()
        
        for row in selected_rows:
            if row < len(self.filtered_data):
                selected_data.append(self.filtered_data[row])
        
        return selected_data
    
    def get_selected_identifiers(self):
        """获取选中项的标识符"""
        identifiers = []
        selected_rows = self.get_selected_rows()
        
        for row in selected_rows:
            if row < len(self.filtered_data):
                # 使用第一个列作为标识符
                first_col = list(self.column_config.keys())[0]
                identifier = self.filtered_data[row].get(first_col)
                if identifier:
                    identifiers.append(identifier)
        
        return identifiers
    
    def restore_selection(self, identifiers):
        """恢复选择状态"""
        if not identifiers:
            return
        
        first_col = list(self.column_config.keys())[0]
        
        for row in range(self.table.rowCount()):
            if row < len(self.filtered_data):
                item_id = self.filtered_data[row].get(first_col)
                if item_id in identifiers:
                    checkbox = self.table.cellWidget(row, 0)
                    if checkbox:
                        checkbox.setChecked(True)
    
    def on_selection_changed(self):
        """选择变化处理"""
        selected_data = self.get_selected_data()
        self.selection_changed.emit(selected_data)
        self.update_status()
    
    def on_checkbox_changed(self, row, state):
        """复选框变化处理"""
        self.on_selection_changed()
    
    def on_column_visibility_changed(self, text):
        """列可见性变化"""
        if text == "显示所有列":
            for i in range(1, self.table.columnCount()):
                self.table.setColumnHidden(i, False)
        else:
            col_name = text.replace("隐藏: ", "")
            col_index = list(self.column_config.keys()).index(col_name) + 1
            is_hidden = self.table.isColumnHidden(col_index)
            self.table.setColumnHidden(col_index, not is_hidden)
    
    def show_context_menu(self, position):
        """显示右键菜单"""
        if self.table.itemAt(position) is None:
            return
        
        menu = QMenu(self)
        
        # 选择操作
        select_all_action = QAction("全选", self)
        select_all_action.triggered.connect(lambda: self.select_all_btn.setChecked(True) or self.toggle_select_all())
        menu.addAction(select_all_action)
        
        select_none_action = QAction("取消全选", self)
        select_none_action.triggered.connect(lambda: self.select_all_btn.setChecked(False) or self.toggle_select_all())
        menu.addAction(select_none_action)
        
        menu.addSeparator()
        
        # 业务操作
        selected_count = len(self.get_selected_rows())
        if selected_count > 0:
            delete_action = QAction(f"删除选中 ({selected_count})", self)
            delete_action.triggered.connect(lambda: self.action_requested.emit("delete", self.get_selected_data()))
            menu.addAction(delete_action)
            
            backup_action = QAction(f"备份选中 ({selected_count})", self)
            backup_action.triggered.connect(lambda: self.action_requested.emit("backup", self.get_selected_data()))
            menu.addAction(backup_action)
        
        menu.exec_(self.table.mapToGlobal(position))
    
    def update_status(self):
        """更新状态信息"""
        total_count = len(self.data_cache)
        filtered_count = len(self.filtered_data)
        selected_count = len(self.get_selected_rows())
        
        if filtered_count != total_count:
            self.info_label.setText(f"显示 {filtered_count}/{total_count} 项")
        else:
            self.info_label.setText("就绪")
        
        if selected_count > 0:
            self.count_label.setText(f"已选择 {selected_count} 项")
        else:
            self.count_label.setText(f"{filtered_count} 项")
    
    def refresh_data(self):
        """刷新数据（由外部实现）"""
        # 发出刷新请求信号
        self.action_requested.emit("refresh", [])
