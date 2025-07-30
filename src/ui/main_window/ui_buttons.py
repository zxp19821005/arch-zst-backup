# -*- coding: utf-8 -*-
"""按钮操作混入类"""

from PySide6.QtWidgets import QPushButton, QMessageBox, QInputDialog
from PySide6.QtCore import QThread, Signal

class UIButtonsMixin:
    """UI按钮操作相关的方法混入类"""
    
    def setup_action_buttons(self, parent_layout):
        """设置操作按钮"""
        from PySide6.QtWidgets import QHBoxLayout
        
        button_layout = QHBoxLayout()
        parent_layout.addLayout(button_layout)
        
        # 删除按钮
        self.delete_button = QPushButton("删除选中")
        self.delete_button.clicked.connect(self.delete_selected)
        self.delete_button.setEnabled(False)
        button_layout.addWidget(self.delete_button)
        
        # 备份按钮
        self.backup_button = QPushButton("备份选中")
        self.backup_button.clicked.connect(self.backup_selected)
        self.backup_button.setEnabled(False)
        button_layout.addWidget(self.backup_button)
        
        # 还原按钮
        self.restore_button = QPushButton("还原选中")
        self.restore_button.clicked.connect(self.restore_selected)
        self.restore_button.setEnabled(False)
        button_layout.addWidget(self.restore_button)
        
        # 弹性空间
        button_layout.addStretch()
        
        return button_layout
    
    def update_button_states(self):
        """更新按钮状态"""
        if hasattr(self, 'current_table'):
            selected_count = len(self.get_selected_rows(self.current_table))
            has_selection = selected_count > 0
            
            if hasattr(self, 'delete_button'):
                self.delete_button.setEnabled(has_selection)
            if hasattr(self, 'backup_button'):
                self.backup_button.setEnabled(has_selection)
            if hasattr(self, 'restore_button'):
                self.restore_button.setEnabled(has_selection)
    
    def delete_selected(self):
        """删除选中项"""
        if not hasattr(self, 'current_table'):
            return
        
        selected_rows = self.get_selected_rows(self.current_table)
        if not selected_rows:
            QMessageBox.warning(self, "警告", "请先选择要删除的项目")
            return
        
        reply = QMessageBox.question(
            self, "确认删除", 
            f"确定要删除选中的 {len(selected_rows)} 个项目吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.perform_delete_operation(selected_rows)
    
    def backup_selected(self):
        """备份选中项"""
        if not hasattr(self, 'current_table'):
            return
        
        selected_rows = self.get_selected_rows(self.current_table)
        if not selected_rows:
            QMessageBox.warning(self, "警告", "请先选择要备份的项目")
            return
        
        self.perform_backup_operation(selected_rows)
    
    def restore_selected(self):
        """还原选中项"""
        if not hasattr(self, 'current_table'):
            return
        
        selected_rows = self.get_selected_rows(self.current_table)
        if not selected_rows:
            QMessageBox.warning(self, "警告", "请先选择要还原的项目")
            return
        
        reply = QMessageBox.question(
            self, "确认还原", 
            f"确定要还原选中的 {len(selected_rows)} 个项目吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.perform_restore_operation(selected_rows)
    
    def perform_delete_operation(self, selected_rows):
        """执行删除操作 - 子类实现"""
        self.logger.info(f"删除操作：{len(selected_rows)} 个项目")
        self.update_status("正在删除...")
    
    def perform_backup_operation(self, selected_rows):
        """执行备份操作 - 子类实现"""
        self.logger.info(f"备份操作：{len(selected_rows)} 个项目")
        self.update_status("正在备份...")
    
    def perform_restore_operation(self, selected_rows):
        """执行还原操作 - 子类实现"""
        self.logger.info(f"还原操作：{len(selected_rows)} 个项目")
        self.update_status("正在还原...")
    
    def show_progress_dialog(self, title, message):
        """显示进度对话框"""
        from PySide6.QtWidgets import QProgressDialog
        
        progress = QProgressDialog(message, "取消", 0, 100, self)
        progress.setWindowTitle(title)
        progress.setWindowModality(Qt.WindowModal)
        progress.show()
        return progress
