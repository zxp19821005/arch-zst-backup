#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QTextEdit, QMessageBox, QFrame, QComboBox,
    QGroupBox, QCheckBox, QRadioButton, QButtonGroup
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from modules.logger import log
from modules.config_manager import config_manager

class SettingsPage(QWidget):
    """设置页面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        log.info("初始化设置页面")
        self.setup_ui()
        self.setup_list_display_settings()
        self.load_settings()

    def setup_list_display_settings(self):
        """设置列表显示列的配置选项"""
        from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QComboBox
        
        self.display_columns_group = QGroupBox("列表显示设置")
        self.display_columns_layout = QVBoxLayout()
        
        # 获取备份软件管理的列名作为标准
        self.column_options = ["名称", "Epoch", "版本", "发布号", "架构", "位置"]
        
        # 创建设置表格
        self.display_table = QTableWidget()
        self.display_table.setColumnCount(3)
        self.display_table.setHorizontalHeaderLabels(["表格列名", "对齐方式", "是否显示"])
        self.display_table.setRowCount(len(self.column_options))
        self.display_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # 设置表头居中
        for i in range(self.display_table.columnCount()):
            item = self.display_table.horizontalHeaderItem(i)
            if item:
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 填充表格内容
        for row, column in enumerate(self.column_options):
            # 列名
            name_item = QTableWidgetItem(column)
            name_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            name_item.setFlags(Qt.ItemIsEnabled)  # 列名不可编辑
            self.display_table.setItem(row, 0, name_item)
            
            # 对齐方式下拉框
            align_combo = QComboBox()
            align_combo.addItems(["靠左显示", "居中显示", "靠右显示"])
            align_combo.setCurrentIndex(1)  # 默认居中
            self.display_table.setCellWidget(row, 1, align_combo)
            
            # 是否显示复选框
            show_check = QCheckBox()
            show_check.setChecked(True)
            show_check.setStyleSheet("margin-left:50%; margin-right:50%;")
            self.display_table.setCellWidget(row, 2, show_check)
        
        self.display_columns_layout.addWidget(self.display_table)
        self.display_columns_group.setLayout(self.display_columns_layout)
        self.layout().addWidget(self.display_columns_group)

    def setup_alignment_settings(self):
        """设置列表内容对齐方式的配置选项"""
        self.alignment_group = QGroupBox("列表内容对齐方式")
        self.alignment_layout = QVBoxLayout()
        
        # 为每个列添加对齐方式设置
        for column in self.column_options:
            group = QGroupBox(f"{column}对齐方式")
            layout = QHBoxLayout()
            
            buttons = QButtonGroup()
            for i, alignment in enumerate(["靠左", "居中", "靠右"]):
                radio = QRadioButton(alignment)
                buttons.addButton(radio, i)
                layout.addWidget(radio)
                
                # 默认选中靠左对齐
                if i == 0:
                    radio.setChecked(True)
            
            group.setLayout(layout)
            self.alignment_layout.addWidget(group)
            setattr(self, f"{column}_alignment_buttons", buttons)
        
        self.alignment_group.setLayout(self.alignment_layout)
        self.layout().addWidget(self.alignment_group)
    
    def setup_ui(self):
        """设置页面UI"""
        main_layout = QVBoxLayout()
        
        # 备份目录设置 - 内嵌式
        backup_frame = QFrame()
        backup_frame.setFrameShape(QFrame.Shape.StyledPanel)
        backup_layout = QHBoxLayout(backup_frame)
        backup_layout.setSpacing(5)
        
        backup_dir_label = QLabel("备份目录:")
        backup_dir_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.backup_dir_edit = QLineEdit()
        
        backup_layout.addWidget(backup_dir_label)
        backup_layout.addWidget(self.backup_dir_edit, 1)
        main_layout.addWidget(backup_frame)
        
        # 缓存目录设置 - 内嵌式
        cache_frame = QFrame()
        cache_frame.setFrameShape(QFrame.Shape.StyledPanel)
        cache_layout = QVBoxLayout(cache_frame)
        cache_layout.setSpacing(5)

        # 关闭行为设置 - 内嵌式
        close_frame = QFrame()
        close_frame.setFrameShape(QFrame.Shape.StyledPanel)
        close_layout = QHBoxLayout(close_frame)
        close_layout.setSpacing(5)
        
        close_label = QLabel("关闭行为:")
        close_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.close_behavior_combo = QComboBox()
        self.close_behavior_combo.addItems(["直接退出程序", "最小化到系统托盘"])
        
        close_layout.addWidget(close_label)
        close_layout.addWidget(self.close_behavior_combo, 1)
        main_layout.addWidget(close_frame)

        # 日志级别设置 - 内嵌式
        log_frame = QFrame()
        log_frame.setFrameShape(QFrame.Shape.StyledPanel)
        log_layout = QHBoxLayout(log_frame)
        log_layout.setSpacing(5)
        
        log_label = QLabel("日志级别:")
        log_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "SUCCESS"])
        
        log_layout.addWidget(log_label)
        log_layout.addWidget(self.log_level_combo, 1)
        main_layout.addWidget(log_frame)
        
        cache_dirs_label = QLabel("缓存目录(每行一个):")
        cache_dirs_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.cache_dirs_edit = QTextEdit()
        self.cache_dirs_edit.setMaximumHeight(100)
        
        cache_layout.addWidget(cache_dirs_label)
        cache_layout.addWidget(self.cache_dirs_edit, 1)
        main_layout.addWidget(cache_frame)
        
        # 添加伸缩因子使布局更紧凑
        main_layout.addStretch(1)
        
        # 保存按钮
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        
        save_button = QPushButton("保存设置")
        save_button.setIcon(QIcon.fromTheme("document-save"))
        save_button.clicked.connect(self.save_settings)
        
        button_layout.addStretch(1)  # 添加伸缩因子
        button_layout.addWidget(save_button)
        
        main_layout.addWidget(button_container)
        
        self.setLayout(main_layout)
        log.info("设置页面UI初始化完成")
    
    def load_settings(self):
        """加载当前设置"""
        config = config_manager.load_config()
        self.backup_dir_edit.setText(config['backupDir'])
        self.cache_dirs_edit.setPlainText("\n".join(config['cacheDirs']))
        
        # 加载关闭行为设置，默认为"直接退出程序"
        close_behavior = config.get('closeBehavior', 'exit')
        if close_behavior == 'minimize':
            self.close_behavior_combo.setCurrentIndex(1)
        else:
            self.close_behavior_combo.setCurrentIndex(0)
            
        # 加载日志级别设置，默认为"INFO"
        log_level = config.get('logLevel', 'INFO')
        index = self.log_level_combo.findText(log_level)
        if index >= 0:
            self.log_level_combo.setCurrentIndex(index)
            
        # 加载表格显示设置
        display_settings = config.get('displaySettings', {})
        # 初始化对齐方式设置
        if 'alignment' not in display_settings:
            display_settings['alignment'] = {
                "名称": "left",
                "Epoch": "center",
                "版本": "center",
                "发布号": "center",
                "架构": "center",
                "位置": "left"
            }
        for row in range(self.display_table.rowCount()):
            # 获取列名（现在索引为0，因为删除了序号列）
            name_item = self.display_table.item(row, 0)
            if not name_item:
                continue
                
            column_name = name_item.text()
            settings = display_settings.get(column_name, {
                'alignment': "center",  # 默认居中
                'visible': True
            })
            
            # 设置对齐方式（现在索引为1）
            align_combo = self.display_table.cellWidget(row, 1)
            if align_combo:
                if settings['alignment'] == "left":
                    align_combo.setCurrentIndex(0)
                elif settings['alignment'] == "right":
                    align_combo.setCurrentIndex(2)
                else:
                    align_combo.setCurrentIndex(1)  # 默认居中
            
            # 设置是否显示（现在索引为2）
            show_check = self.display_table.cellWidget(row, 2)
            if show_check:
                show_check.setChecked(settings['visible'])
            
        log.info("加载当前设置完成")
    
    def save_settings(self):
        """保存设置"""
        backup_dir = self.backup_dir_edit.text().strip()
        cache_dirs = [
            dir.strip() for dir in self.cache_dirs_edit.toPlainText().split("\n") 
            if dir.strip()
        ]
        
        # 获取关闭行为设置
        close_behavior = 'minimize' if self.close_behavior_combo.currentIndex() == 1 else 'exit'
        
        # 获取表格显示设置
        display_settings = {}
        for row in range(self.display_table.rowCount()):
            # 修正列名获取逻辑，从第0列获取
            name_item = self.display_table.item(row, 0)
            if not name_item:
                continue
            column_name = name_item.text()
            align_combo = self.display_table.cellWidget(row, 1)
            show_check = self.display_table.cellWidget(row, 2)
            
            # 获取对齐方式
            align_text = align_combo.currentText()
            if align_text == "靠左显示":
                alignment = "left"
            elif align_text == "居中显示":
                alignment = "center"
            else:
                alignment = "right"
            
            display_settings[column_name] = {
                'alignment': alignment,
                'visible': show_check.isChecked()
            }
        
        config = {
            'backupDir': backup_dir,
            'cacheDirs': cache_dirs,
            'closeBehavior': close_behavior,
            'logLevel': self.log_level_combo.currentText(),
            'displaySettings': display_settings
        }
        
        if not backup_dir:
            QMessageBox.warning(self, "警告", "备份目录不能为空")
            log.warning("尝试保存空备份目录")
            return
        
        if not cache_dirs:
            QMessageBox.warning(self, "警告", "至少需要一个缓存目录")
            log.warning("尝试保存空缓存目录列表")
            return
        
        if config_manager.save_config(config):
            QMessageBox.information(self, "成功", "设置已保存")
            log.success("设置保存成功")
        else:
            QMessageBox.critical(self, "错误", "保存设置失败")
            log.error("设置保存失败")