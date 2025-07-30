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
from src.modules.logger import log
from src.modules.config_manager import config_manager
from src.modules.directory_scanner import directory_scanner
from src.modules.file_operations import file_operations
from modules.version_comparator import version_comparator
from modules.list_display_manager import TableDisplayManager

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
        self.table.horizontalHeader().setStretchLastSection(True)

        # 使用预定义的列配置
        from modules.list_display_manager import COLUMN_CONFIGS
        column_config = COLUMN_CONFIGS["backup_manager"]
        column_names = list(column_config.keys())
        self.list_display_manager = TableDisplayManager(self.table, column_config)
        # 应用 displaySettings 中的列对齐方式
        for column_name, settings in column_config.items():
            column_index = list(column_config.keys()).index(column_name)
            alignment = settings.get("alignment", "left")
            if alignment == "center":
                self.table.horizontalHeader().setDefaultAlignment(Qt.AlignCenter)
            elif alignment == "right":
                self.table.horizontalHeader().setDefaultAlignment(Qt.AlignRight)
            else:
                self.table.horizontalHeader().setDefaultAlignment(Qt.AlignLeft)
        main_layout.addWidget(self.table)
        self.table.setVisible(True)  # 显式设置表格可见
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
        self.list_display_manager.update_table(self.packages)
    
    
    
    def get_selected_packages(self):
        """获取选中的软件包"""
        return self.list_display_manager.get_selected_packages(self.packages)
    
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