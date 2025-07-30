# -*- coding: utf-8 -*-
"""表格操作混入类"""

from PySide6.QtWidgets import QTableWidgetItem, QCheckBox, QHeaderView
from PySide6.QtCore import Qt
from datetime import datetime

class TableOperationsMixin:
    """表格操作相关的方法混入类"""
    
    def setup_table(self, table_widget, columns):
        """设置表格"""
        table_widget.setColumnCount(len(columns) + 1)  # +1 为选择列
        headers = ["选择"] + columns
        table_widget.setHorizontalHeaderLabels(headers)
        
        # 设置表格属性
        table_widget.setSelectionBehavior(table_widget.SelectionBehavior.SelectRows)
        table_widget.setAlternatingRowColors(True)
        table_widget.setSortingEnabled(True)
        
        # 调整列宽
        header = table_widget.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # 选择列固定宽度
        header.resizeSection(0, 50)
        
        for i in range(1, len(headers)):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)
        
        # 隐藏行号
        table_widget.verticalHeader().setVisible(False)
        
        # 连接选择变化信号
        table_widget.itemSelectionChanged.connect(self.on_selection_changed)
        
        return table_widget
    
    def update_table_data(self, table_widget, data_list, column_config):
        """更新表格数据"""
        # 保存当前滚动位置
        scrollbar = table_widget.verticalScrollBar()
        scroll_position = scrollbar.value()
        
        # 保存选择状态
        selected_items = self.get_selected_items(table_widget)
        
        table_widget.setRowCount(len(data_list))
        
        for row, item_data in enumerate(data_list):
            # 添加选择框
            checkbox = QCheckBox()
            checkbox.setChecked(False)
            checkbox.stateChanged.connect(lambda state, r=row: self.on_checkbox_changed(r, state))
            table_widget.setCellWidget(row, 0, checkbox)
            
            # 添加数据列
            for col, (column_key, config) in enumerate(column_config.items(), start=1):
                value = item_data.get(column_key, "")
                
                # 根据数据类型格式化
                data_type = config.get('type', 'str')
                if data_type == 'datetime' and value:
                    value = datetime.fromisoformat(value).strftime("%Y-%m-%d %H:%M:%S")
                
                table_item = QTableWidgetItem(str(value))
                
                # 设置对齐方式
                alignment = config.get('alignment', 'left')
                if alignment == 'center':
                    table_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                elif alignment == 'right':
                    table_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
                else:
                    table_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft)
                
                # 设置只读
                table_item.setFlags(table_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                
                # 添加工具提示
                tooltip = config.get('tooltip')
                if tooltip:
                    table_item.setToolTip(tooltip)
                
                table_widget.setItem(row, col, table_item)
        
        # 恢复选择状态
        self.restore_selection(table_widget, selected_items)
        
        # 恢复滚动位置
        scrollbar.setValue(scroll_position)
        
        self.logger.info(f"表格数据更新完成，共 {len(data_list)} 行")
    
    def get_selected_items(self, table_widget):
        """获取选中项的标识符"""
        selected_items = []
        for row in range(table_widget.rowCount()):
            checkbox = table_widget.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                # 使用第一列作为标识符
                name_item = table_widget.item(row, 1)
                if name_item:
                    selected_items.append(name_item.text())
        return selected_items
    
    def restore_selection(self, table_widget, selected_items):
        """恢复选择状态"""
        for row in range(table_widget.rowCount()):
            name_item = table_widget.item(row, 1)
            if name_item and name_item.text() in selected_items:
                checkbox = table_widget.cellWidget(row, 0)
                if checkbox:
                    checkbox.setChecked(True)
    
    def get_selected_rows(self, table_widget):
        """获取选中的行"""
        selected_rows = []
        for row in range(table_widget.rowCount()):
            checkbox = table_widget.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                selected_rows.append(row)
        return selected_rows
    
    def toggle_select_all(self):
        """切换全选状态"""
        if hasattr(self, 'current_table'):
            is_checked = self.select_all_button.isChecked()
            
            for row in range(self.current_table.rowCount()):
                checkbox = self.current_table.cellWidget(row, 0)
                if checkbox:
                    checkbox.setChecked(is_checked)
            
            text = "取消全选" if is_checked else "全选"
            self.select_all_button.setText(text)
    
    def filter_packages(self, text):
        """过滤软件包"""
        if hasattr(self, 'current_table'):
            visible_count = 0
            for row in range(self.current_table.rowCount()):
                should_show = True
                if text:
                    # 检查所有列是否包含搜索文本
                    should_show = False
                    for col in range(1, self.current_table.columnCount()):
                        item = self.current_table.item(row, col)
                        if item and text.lower() in item.text().lower():
                            should_show = True
                            break
                
                self.current_table.setRowHidden(row, not should_show)
                if should_show:
                    visible_count += 1
            
            self.update_status(f"显示 {visible_count} 项")
    
    def on_selection_changed(self):
        """选择变化处理"""
        if hasattr(self, 'current_table'):
            selected_count = len(self.get_selected_rows(self.current_table))
            if selected_count > 0:
                self.update_status(f"已选择 {selected_count} 项")
            else:
                self.update_status("就绪")
    
    def on_checkbox_changed(self, row, state):
        """复选框状态变化处理"""
        self.on_selection_changed()
    
    def refresh_data(self):
        """刷新数据"""
        # 子类需要实现具体的刷新逻辑
        self.logger.info("刷新数据")
        self.update_status("正在刷新数据...")
