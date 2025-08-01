#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTextEdit, QMessageBox, QFrame, QComboBox,
    QGroupBox, QCheckBox, QRadioButton, QButtonGroup, QTableWidget, QHeaderView, QTableWidgetItem
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from src.modules.logger import log
from src.modules.config_manager import config_manager
from ui.components.button_style import ButtonStyle

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
        pass

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
        main_layout.setContentsMargins(5, 5, 5, 5)

        # 目录设置 - 合并式
        dir_group = QGroupBox("目录设置")
        dir_group.setMaximumHeight(100)
        dir_layout = QHBoxLayout(dir_group)
        dir_layout.setContentsMargins(5, 5, 5, 5)
        dir_layout.setSpacing(10)

        # 备份目录设置 - 左侧
        backup_group = QGroupBox("备份目录")
        backup_layout = QVBoxLayout(backup_group)
        backup_layout.setContentsMargins(5, 5, 5, 5)
        backup_layout.setSpacing(5)

        self.backup_dir_edit = QLineEdit()
        self.backup_dir_edit.setMaximumHeight(25)

        backup_layout.addWidget(self.backup_dir_edit)
        backup_layout.addStretch(0)
        dir_layout.addWidget(backup_group)

        # 缓存目录设置 - 右侧
        cache_group = QGroupBox("缓存目录")
        cache_layout = QVBoxLayout(cache_group)
        cache_layout.setContentsMargins(5, 5, 5, 5)
        cache_layout.setSpacing(5)

        # 创建水平布局用于并排显示复选框
        cache_check_layout = QHBoxLayout()
        cache_check_layout.setSpacing(10)
        
        # 系统缓存复选框
        self.system_cache_check = QCheckBox("系统缓存")
        self.system_cache_check.setToolTip("/var/cache/pacman/pkg/")
        
        # paru缓存复选框
        self.paru_cache_check = QCheckBox("paru缓存")
        self.paru_cache_check.setToolTip("~/.cache/paru/clone/")
        
        # yay缓存复选框
        self.yay_cache_check = QCheckBox("yay缓存")
        self.yay_cache_check.setToolTip("~/.cache/yay/")

        # 将复选框添加到水平布局中
        cache_check_layout.addWidget(self.system_cache_check)
        cache_check_layout.addWidget(self.paru_cache_check)
        cache_check_layout.addWidget(self.yay_cache_check)
        cache_check_layout.addStretch(1)
        
        # 将水平布局添加到垂直布局中
        cache_layout.addLayout(cache_check_layout)
        dir_layout.addWidget(cache_group)
        main_layout.addWidget(dir_group)

        # 关闭行为和日志级别设置 - 并排显示
        behavior_log_layout = QHBoxLayout()
        behavior_log_layout.setContentsMargins(5, 5, 5, 5)
        behavior_log_layout.setSpacing(10)
        
        # 关闭行为设置 - 左侧
        close_group = QGroupBox("关闭行为")
        close_layout = QHBoxLayout(close_group)
        close_layout.setContentsMargins(5, 5, 5, 5)
        
        close_label = QLabel("关闭行为:")
        close_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.close_behavior_combo = QComboBox()
        self.close_behavior_combo.addItems(["直接退出程序", "最小化到系统托盘"])
        
        close_layout.addWidget(close_label)
        close_layout.addWidget(self.close_behavior_combo, 1)
        
        # 日志管理设置 - 右侧
        log_group = QGroupBox("日志管理")
        log_layout = QVBoxLayout(log_group)
        log_layout.setSpacing(5)
        log_layout.setContentsMargins(5, 5, 5, 5)
        
        # 日志保存天数设置
        retention_layout = QHBoxLayout()
        retention_label = QLabel("日志保存天数:")
        retention_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.log_retention_edit = QLineEdit("30")
        self.log_retention_edit.setMaximumHeight(25)
        retention_layout.addWidget(retention_label)
        retention_layout.addWidget(self.log_retention_edit, 1)

        

        
        log_layout.addLayout(retention_layout)
        
        # 将两个设置组添加到水平布局中
        behavior_log_layout.addWidget(close_group)
        behavior_log_layout.addWidget(log_group)
        
        # 将水平布局添加到主布局中
        main_layout.addLayout(behavior_log_layout)

        # 列表显示设置
        self.display_columns_group = QGroupBox("列表显示设置")
        self.display_columns_layout = QVBoxLayout()

        # 获取备份软件管理的列名作为标准
        self.column_options = ["名称", "epoch", "版本", "发布号", "架构", "位置"]

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
        self.display_columns_layout.setContentsMargins(5, 5, 5, 5)
        self.display_columns_layout.setSpacing(0)
        self.display_columns_group.setLayout(self.display_columns_layout)
        self.display_columns_group.setContentsMargins(5, 5, 5, 5)
        main_layout.addWidget(self.display_columns_group)

        # 保存按钮
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(10, 5, 10, 5)

        save_button = QPushButton("保存设置")
        save_button.clicked.connect(self.save_settings)
        ButtonStyle.apply_success_style(save_button)

        button_layout.addStretch(1)  # 添加左侧伸缩因子
        button_layout.addWidget(save_button)
        # 不添加右侧伸缩因子，使按钮靠右显示

        main_layout.addWidget(button_container)

        self.setLayout(main_layout)
        log.info("设置页面UI初始化完成")

    def load_settings(self):
        """加载当前设置"""
        config = config_manager.load_config()
        self.backup_dir_edit.setText(config.get('backupDir', ''))

        # 安全地获取cacheDirs，如果不存在则使用空列表
        cache_dirs = config.get('cacheDirs', [])
        
        # 定义缓存目录路径
        system_cache_path = "/var/cache/pacman/pkg/"
        paru_cache_path = os.path.expanduser("~/.cache/paru/clone/")
        yay_cache_path = os.path.expanduser("~/.cache/yay/")
        
        # 根据配置设置复选框状态
        self.system_cache_check.setChecked(system_cache_path in cache_dirs)
        self.paru_cache_check.setChecked(paru_cache_path in cache_dirs)
        self.yay_cache_check.setChecked(yay_cache_path in cache_dirs)

        # 加载关闭行为设置，默认为"直接退出程序"
        close_behavior = config.get('closeBehavior', 'exit')
        if close_behavior == 'minimize':
            self.close_behavior_combo.setCurrentIndex(1)
        else:
            self.close_behavior_combo.setCurrentIndex(0)

        # 加载日志保存天数设置，默认为30天
        log_retention = config.get('logRetentionDays', 30)
        self.log_retention_edit.setText(str(log_retention))

        # 加载表格显示设置
        display_settings = config.get('displaySettings', {})
        # 初始化对齐方式设置，使用英文列名
        if 'alignment' not in display_settings:
            display_settings['alignment'] = {
                "name": "left",
                "epoch": "center",
                "version": "center",
                "pkgrel": "center",
                "arch": "center",
                "location": "left"
            }
        for row in range(self.display_table.rowCount()):
            # 获取列名（现在索引为0，因为删除了序号列）
            name_item = self.display_table.item(row, 0)
            if not name_item:
                continue

            column_name = name_item.text()

            # 创建英文列名到中文列名的映射
            english_to_chinese = {
                "name": "名称",
                "epoch": "epoch",
                "version": "版本",
                "pkgrel": "发布号",
                "arch": "架构",
                "location": "位置"
            }

            # 尝试从配置中获取设置，先尝试中文列名，再尝试英文列名
            settings = display_settings.get(column_name, None)
            if settings is None:
                # 如果中文列名找不到，尝试对应的英文列名
                for eng, chn in english_to_chinese.items():
                    if chn == column_name and eng in display_settings.get('alignment', {}):
                        settings = {
                            'alignment': display_settings['alignment'][eng],
                            'visible': display_settings.get('visibility', {}).get(eng, True)
                        }
                        break

            # 如果还是找不到，使用默认值
            if settings is None:
                settings = {
                    'alignment': "center",  # 默认居中
                    'visible': True
                }

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
        
        # 根据复选框状态构建缓存目录列表
        cache_dirs = []
        if self.system_cache_check.isChecked():
            cache_dirs.append("/var/cache/pacman/pkg/")
        if self.paru_cache_check.isChecked():
            cache_dirs.append(os.path.expanduser("~/.cache/paru/clone/"))
        if self.yay_cache_check.isChecked():
            cache_dirs.append(os.path.expanduser("~/.cache/yay/"))

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

            # 创建中文列名到英文列名的映射
            column_mapping = {
                "名称": "name",
                "epoch": "epoch",
                "版本": "version",
                "发布号": "pkgrel",
                "架构": "arch",
                "位置": "location"
            }

            # 使用英文列名保存配置
            english_column_name = column_mapping.get(column_name, column_name.lower())
            display_settings[english_column_name] = {
                'alignment': alignment,
                'visible': show_check.isChecked()
            }

        # 获取日志保存天数设置
        try:
            log_retention = int(self.log_retention_edit.text().strip())
            if log_retention < 1:
                log_retention = 30  # 默认值
                self.log_retention_edit.setText("30")
        except ValueError:
            log_retention = 30  # 默认值
            self.log_retention_edit.setText("30")
            
        config = {
            'backupDir': backup_dir,
            'cacheDirs': cache_dirs,
            'closeBehavior': close_behavior,
            'logRetentionDays': log_retention,
            'displaySettings': {
                'alignment': {k: v['alignment'] for k, v in display_settings.items()},
                'visibility': {k: v['visible'] for k, v in display_settings.items()}
            }
        }

        config_manager.save_config(config)
        msg_box = QMessageBox(QMessageBox.Information, "保存成功", "设置已成功保存！")
        ok_btn = msg_box.addButton("确定", QMessageBox.AcceptRole)
        ButtonStyle.apply_primary_style(ok_btn)
        msg_box.exec()
        log.info("设置已保存")