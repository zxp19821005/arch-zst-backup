#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QCheckBox, QHeaderView,
    QMessageBox
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon
from modules.logger import log
from modules.config_manager import config_manager
from modules.directory_scanner import directory_scanner
from modules.file_operations import file_operations
from modules.version_comparator import version_comparator

class BackupManagerPage(QWidget):
    """备份软件管理页面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        log.info("初始化备份软件管理页面")
        self.packages = []
        self.setup_ui()
        self.load_existing_packages()
    
    def setup_ui(self):
        """设置页面UI"""
        main_layout = QVBoxLayout()
        
        # 按钮栏
        button_layout = QHBoxLayout()
        
        # 全选复选框
        self.select_all_checkbox = QCheckBox("全选")
        self.select_all_checkbox.stateChanged.connect(self.toggle_select_all)
        button_layout.addWidget(self.select_all_checkbox)
        
        # 按钮布局
        button_layout.addStretch()  # 将按钮推到右侧
        
        # 刷新按钮
        self.scan_button = QPushButton("刷新")
        self.scan_button.clicked.connect(self.scan_backup_dir)
        button_layout.addWidget(self.scan_button)
        
        # 去重按钮
        self.dedupe_button = QPushButton("去重")
        self.dedupe_button.clicked.connect(self.deduplicate_packages)
        button_layout.addWidget(self.dedupe_button)
        
        # 删除按钮
        self.delete_button = QPushButton("删除")
        self.delete_button.clicked.connect(self.delete_selected)
        button_layout.addWidget(self.delete_button)
        main_layout.addLayout(button_layout)
        
        # 软件包表格
        self.table = QTableWidget()
        
        # 从配置加载显示设置
        config = config_manager.load_config()
        display_settings = config.get('displaySettings', {})
        
        # 默认列设置
        default_columns = ["选择", "名称", "Epoch", "版本", "发布号", "架构", "位置"]
        
        # 应用可见性设置
        visible_columns = []
        column_indices = {}  # 保存列名到索引的映射
        for i, col in enumerate(default_columns[1:]):  # 跳过"选择"列
            display_setting = display_settings.get(col, {})
            if display_setting.get('visible', True):
                visible_columns.append(col)
                column_indices[col] = i + 1  # 记录可见列的索引
        
        # 设置表格列数
        self.table.setColumnCount(len(visible_columns) + 1)  # +1 为"选择"列

        # 隐藏不可见的列
        for i, col in enumerate(default_columns[1:], start=1):  # 从1开始跳过"选择"列
            if col not in visible_columns:
                self.table.setColumnHidden(i, True)
        
        # 设置表头
        self.table.setHorizontalHeaderLabels(["选择"] + visible_columns)
        
        # 设置列宽调整模式
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        
        # 设置表头居中
        header = self.table.horizontalHeader()
        header.setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)

        # 应用对齐方式设置
        for col_name in visible_columns:
            col_index = column_indices[col_name]
            alignment = display_settings.get(col_name, {}).get('alignment', "center")
            align_flag = Qt.AlignmentFlag.AlignCenter
            if alignment == "left":
                align_flag = Qt.AlignmentFlag.AlignLeft
            elif alignment == "right":
                align_flag = Qt.AlignmentFlag.AlignRight

            # 设置列的对齐方式
            self.table.horizontalHeaderItem(col_index).setTextAlignment(align_flag | Qt.AlignmentFlag.AlignVCenter)
            
            self.table.horizontalHeaderItem(col).setTextAlignment(align_flag | Qt.AlignmentFlag.AlignVCenter)
        
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        main_layout.addWidget(self.table)
        
        self.setLayout(main_layout)
        log.info("备份软件管理页面UI设置完成")
    
    def load_existing_packages(self):
        """加载现有的软件包列表"""
        config_dir = Path(config_manager.config_dir)
        packages_file = config_dir / "existing_packages.json"
        
        if packages_file.exists():
            try:
                with open(packages_file, 'r', encoding='utf-8') as f:
                    self.packages = json.load(f)
                    self.update_table()
                    log.info(f"从 {packages_file} 加载了 {len(self.packages)} 个软件包")
            except Exception as e:
                log.error(f"加载软件包列表失败: {str(e)}")
                QMessageBox.critical(self, "错误", "加载软件包列表失败")
    
    def scan_backup_dir(self):
        """扫描备份目录"""
        config = config_manager.load_config()
        if not config['backupDir']:
            QMessageBox.warning(self, "警告", "请先在设置中配置备份目录")
            log.warning("未配置备份目录，无法扫描")
            return
        
        self.packages = directory_scanner.scan_directory(config['backupDir'], recursive=True)
        self.update_table()
        
        # 保存扫描结果
        config_dir = Path(config_manager.config_dir)
        packages_file = config_dir / "existing_packages.json"
        
        try:
            # 保存前移除 filename 字段
            packages_to_save = []
            for pkg in self.packages:
                pkg_copy = pkg.copy()
                pkg_copy.pop('filename', None)  # 移除 filename 字段
                packages_to_save.append(pkg_copy)
            
            with open(packages_file, 'w', encoding='utf-8') as f:
                json.dump(packages_to_save, f, indent=4, ensure_ascii=False)
            log.success(f"保存了 {len(self.packages)} 个软件包到 {packages_file}")
        except Exception as e:
            log.error(f"保存软件包列表失败: {str(e)}")
            QMessageBox.critical(self, "错误", "保存软件包列表失败")
    
    def update_table(self):
        """更新表格显示"""
        self.table.setRowCount(len(self.packages))
        
        for row, pkg in enumerate(self.packages):
            # 选择复选框
            checkbox = QCheckBox()
            checkbox.setChecked(False)
            self.table.setCellWidget(row, 0, checkbox)
            
            # 其他信息
            self.table.setItem(row, 1, QTableWidgetItem(pkg.get('name', '')))
            # 只在 epoch 存在且不为 '0' 时显示
            epoch = pkg.get('epoch', '0')
            self.table.setItem(row, 2, QTableWidgetItem(epoch if epoch != '0' else ''))
            self.table.setItem(row, 3, QTableWidgetItem(pkg.get('version', '')))
            self.table.setItem(row, 4, QTableWidgetItem(pkg.get('pkgrel', '')))
            self.table.setItem(row, 5, QTableWidgetItem(pkg.get('arch', '')))
            self.table.setItem(row, 6, QTableWidgetItem(pkg.get('location', '')))
        
        log.info(f"更新表格显示，共 {len(self.packages)} 行")
    
    def toggle_select_all(self, state):
        """全选/取消全选"""
        is_checked = self.select_all_checkbox.isChecked()
        for row in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(row, 0)
            if checkbox:
                checkbox.setChecked(is_checked)
        log.info(f"{'全选' if is_checked else '取消全选'}所有软件包")
    
    def get_selected_packages(self):
        """获取选中的软件包"""
        selected = []
        for row in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                selected.append(self.packages[row])
        return selected
    
    def deduplicate_packages(self):
        """去重软件包"""
        if not self.packages:
            QMessageBox.warning(self, "警告", "没有可处理的软件包，请先扫描备份目录")
            return
        
        # 按名称和架构分组软件包
        grouped = {}
        for pkg in self.packages:
            key = (pkg['name'], pkg['arch'])
            grouped.setdefault(key, []).append(pkg)
        
        # 找出需要删除的旧版本
        to_delete = []
        for (name, arch), pkgs in grouped.items():
            if len(pkgs) > 1:
                latest = version_comparator.find_latest(pkgs)
                for pkg in pkgs:
                    if pkg != latest:
                        to_delete.append(pkg)
        
        if not to_delete:
            QMessageBox.information(self, "信息", "没有找到可去重的软件包")
            return
        
        # 确认删除
        confirm = QMessageBox.question(
            self, "确认去重",
            f"确定要删除 {len(to_delete)} 个旧版本软件包吗？\n"
            f"将保留每个软件包的最新版本。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.No:
            return
        
        # 执行删除
        success_count = 0
        failed_files = []
        
        for pkg in to_delete:
            file_path = Path(pkg['location']) / pkg['filename']
            try:
                if file_operations.delete_file(str(file_path)):
                    success_count += 1
                    log.info(f"已删除旧版本: {file_path}")
                else:
                    failed_files.append(str(file_path))
                    log.warning(f"删除旧版本失败: {file_path}")
            except Exception as e:
                log.error(f"删除 {file_path} 时出错: {str(e)}")
                failed_files.append(str(file_path))
        
        # 重新扫描并显示结果
        self.scan_backup_dir()
        
        result_msg = f"成功删除了 {success_count}/{len(to_delete)} 个旧版本"
        if failed_files:
            result_msg += f"\n\n删除失败的文件:\n" + "\n".join(failed_files[:3])
            if len(failed_files) > 3:
                result_msg += f"\n...等共 {len(failed_files)} 个文件"
        
        QMessageBox.information(self, "去重完成", result_msg)
        log.info(f"去重操作结果: {result_msg}")
    
    def delete_selected(self):
        """删除选中的软件包"""
        selected = self.get_selected_packages()
        if not selected:
            QMessageBox.warning(self, "警告", "请先选择要删除的软件包")
            return
        
        confirm = QMessageBox.question(
            self, "确认", 
            f"确定要删除选中的 {len(selected)} 个软件包吗？此操作不可撤销！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            success_count = 0
            for pkg in selected:
                file_path = Path(pkg['location']) / pkg['filename']
                if file_operations.delete_file(str(file_path)):
                    success_count += 1
            
            # 重新加载列表
            self.scan_backup_dir()
            QMessageBox.information(self, "完成", f"成功删除了 {success_count}/{len(selected)} 个软件包")
            log.info(f"删除了 {success_count}/{len(selected)} 个选中的软件包")