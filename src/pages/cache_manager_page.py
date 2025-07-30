#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QCheckBox, QHeaderView,
    QMessageBox
)
from PySide6.QtCore import Qt, QSize, QProcess
from PySide6.QtGui import QIcon
from modules.logger import log
from modules.config_manager import config_manager
from modules.directory_scanner import directory_scanner
from modules.file_operations import file_operations
from modules.package_parser import package_parser
from modules.version_comparator import version_comparator
from modules.list_display_manager import TableDisplayManager

class CacheManagerPage(QWidget):
    """缓存软件管理页面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        log.info("初始化缓存软件管理页面")
        self.packages = []
        self.list_display_manager = None  # 初始化属性
        self.setup_ui()
        self.load_existing_packages()
    
    def setup_ui(self):
        """设置页面UI"""

        main_layout = QVBoxLayout()
        # 操作按钮栏
        button_layout = QHBoxLayout()

        # 按钮布局 - 靠右对齐
        button_layout.addStretch()

        # 刷新按钮
        self.scan_button = QPushButton("刷新")
        self.scan_button.clicked.connect(self.scan_cache_dirs)
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

        # 创建表格
        self.table_widget = QTableWidget()
        self.table_widget.horizontalHeader().setStretchLastSection(True)
        
        # 设置表格颜色
        table_palette = self.table_widget.palette()
        table_palette.setColor(self.table_widget.backgroundRole(), Qt.black)
        table_palette.setColor(self.table_widget.foregroundRole(), Qt.white)
        self.table_widget.setPalette(table_palette)

        # 使用预定义的列配置
        from modules.list_display_manager import COLUMN_CONFIGS
        column_config = COLUMN_CONFIGS["cache_manager"]

        main_layout.addWidget(self.table_widget)
        self.list_display_manager = TableDisplayManager(self.table_widget, column_config)
        # 应用 displaySettings 中的列对齐方式
        for column_name, settings in column_config.items():
            column_index = list(column_config.keys()).index(column_name)
            alignment = settings.get("alignment", "left")
            if alignment == "center":
                self.table_widget.horizontalHeader().setDefaultAlignment(Qt.AlignCenter)
            elif alignment == "right":
                self.table_widget.horizontalHeader().setDefaultAlignment(Qt.AlignRight)
            else:
                self.table_widget.horizontalHeader().setDefaultAlignment(Qt.AlignLeft)
        # 设置页面布局
        self.setLayout(main_layout)
        log.info("缓存软件管理页面UI设置完成")
    
    def load_existing_packages(self):
        """加载现有的软件包列表"""
        config_dir = Path(config_manager.config_dir)
        packages_file = config_dir / "updated_packages.json"
        
        if packages_file.exists():
            try:
                with open(packages_file, 'r', encoding='utf-8') as f:
                    self.packages = json.load(f)
                    if not isinstance(self.packages, list):
                        raise ValueError("Invalid packages data format")
                        
                    if not self.packages:
                        log.warning(f"软件包列表为空: {packages_file}")
                        self.packages = []  # 确保是空列表
                    else:
                        log.info(f"从 {packages_file} 加载了 {len(self.packages)} 个软件包")
                    self.update_table()
            except Exception as e:
                log.error(f"加载软件包列表失败: {str(e)}")
                self.packages = []  # 确保是空列表
                self.update_table()  # 使用空列表更新表格
                QMessageBox.critical(self, "错误", f"加载软件包列表失败: {str(e)}")
    
    def scan_cache_dirs(self):
        """扫描缓存目录"""
        config = config_manager.load_config()
        if not config.get('cacheDirs', []):
            QMessageBox.warning(self, "警告", "请先在设置中配置缓存目录")
            log.warning("未配置缓存目录，无法扫描")
            return
        
        self.packages = []
        for cache_dir in config['cacheDirs']:
            scanned_packages = directory_scanner.scan_directory(cache_dir, recursive=True)
            # 解析包信息
            for pkg in scanned_packages:
                parsed_info = package_parser.parse_filename(Path(pkg['filename']).name)
                if parsed_info:
                    pkg.update(parsed_info)
                    # 获取软件包的实际路径，提取目录部分
                    pkg_path = Path(pkg['fullpath'])
                    dir_path = pkg_path.parent
                    
                    # 检查是否是 pacman 缓存目录
                    expanded_cache_dir = os.path.expanduser(cache_dir)
                    if str(dir_path) == expanded_cache_dir or str(dir_path).startswith(expanded_cache_dir + '/'):
                        # 如果是 pacman 缓存目录，直接使用缓存目录作为位置
                        location = expanded_cache_dir
                    else:
                        # 否则，使用文件所在目录作为位置
                        location = str(dir_path)
                    
                    # 将用户主目录路径替换为 ~ 符号
                    home_dir = os.path.expanduser('~')
                    if location.startswith(home_dir):
                        location = '~' + location[len(home_dir):]
                    
                    # 将特定的缓存目录路径替换为对应的别名
                    paru_cache_path = os.path.expanduser('~/.cache/paru/clone')
                    yay_cache_path = os.path.expanduser('~/.cache/yay')
                    
                    if location == paru_cache_path:
                        location = 'paru_cache'
                    elif location == yay_cache_path:
                        location = 'yay_cache'
                    
                    pkg['location'] = location
                    self.packages.append(pkg)
        
        self.update_table()
        
        # 保存扫描结果
        config_dir = Path(config_manager.config_dir)
        packages_file = config_dir / "updated_packages.json"
        
        try:
            with open(packages_file, 'w', encoding='utf-8') as f:
                json.dump(self.packages, f, indent=4, ensure_ascii=False)
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
        """去重软件包，保留最新版本"""
        if not self.packages:
            QMessageBox.warning(self, "警告", "请先扫描缓存目录")
            return
        
        # 按名称分组
        packages_by_name = {}
        for pkg in self.packages:
            name = pkg['name']
            if name not in packages_by_name:
                packages_by_name[name] = []
            packages_by_name[name].append(pkg)
        
        # 找出需要删除的旧版本
        to_delete = []
        for name, pkgs in packages_by_name.items():
            if len(pkgs) > 1:
                try:
                    # 使用version_comparator找出最新版本
                    latest = version_comparator.find_latest(pkgs)
                    # 删除非最新版本
                    for pkg in pkgs:
                        if pkg != latest:
                            to_delete.append(pkg)
                    log.debug(f"软件包 {name} 保留版本: {latest['version']}-{latest['pkgrel']}")
                except Exception as e:
                    log.error(f"比较软件包 {name} 版本时出错: {str(e)}")
                    continue
        
        if not to_delete:
            QMessageBox.information(self, "信息", "没有发现重复的软件包")
            return
        
        # 显示确认对话框
        confirm = QMessageBox.question(
            self, "确认去重", 
            f"发现 {len(to_delete)} 个旧版本软件包，是否删除？\n"
            "注意: 此操作将永久删除文件且不可恢复！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
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
                except Exception as e:
                    log.error(f"删除文件 {file_path} 失败: {str(e)}")
                    failed_files.append(str(file_path))
            
            # 重新扫描
            self.scan_cache_dirs()
            
            # 显示操作结果
            result_msg = f"成功删除了 {success_count}/{len(to_delete)} 个旧版本软件包"
            if failed_files:
                result_msg += f"\n\n删除失败的文件:\n" + "\n".join(failed_files[:5]) 
                if len(failed_files) > 5:
                    result_msg += f"\n...等共 {len(failed_files)} 个文件"
            
            QMessageBox.information(self, "完成", result_msg)
            log.info(f"去重操作结果: {result_msg}")
    
    def delete_selected(self):
        """删除选中的软件包"""
        selected = self.get_selected_packages()
        if not selected:
            QMessageBox.warning(self, "警告", "请先选择要删除的软件包")
            return
        
        confirm = QMessageBox.question(
            self, "确认删除", 
            f"确定要删除选中的 {len(selected)} 个软件包吗？此操作不可撤销！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            success_count = 0
            failed_files = []
            
            for pkg in selected:
                file_path = Path(pkg['location']) / pkg['filename']
                try:
                    if file_operations.delete_file(str(file_path)):
                        success_count += 1
                        log.info(f"已删除文件: {file_path}")
                    else:
                        failed_files.append(str(file_path))
                        log.warning(f"删除文件失败: {file_path}")
                except Exception as e:
                    log.error(f"删除文件 {file_path} 时出错: {str(e)}")
                    failed_files.append(str(file_path))
            
            # 重新扫描
            self.scan_cache_dirs()
            
            # 显示操作结果
            result_msg = f"成功删除了 {success_count}/{len(selected)} 个软件包"
            if failed_files:
                result_msg += f"\n\n删除失败的文件:\n" + "\n".join(failed_files[:5]) 
                if len(failed_files) > 5:
                    result_msg += f"\n...等共 {len(failed_files)} 个文件"
            
            QMessageBox.information(self, "完成", result_msg)
            log.info(f"删除操作结果: {result_msg}")

    def backup_files(self):
        """备份文件"""
        config = config_manager.load_config()
        if not config.get('backupDirs', []):
            QMessageBox.warning(self, "警告", "请先在设置中配置备份目录")
            log.warning("未配置备份目录，无法备份")
            return

        confirm = QMessageBox.question(
            self, "确认备份",
            "确定要备份选中的文件吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if confirm != QMessageBox.StandardButton.Yes:
            return

        selected = self.get_selected_packages()
        if not selected:
            QMessageBox.warning(self, "警告", "请先选择要备份的文件")
            return

        success_count = 0
        failed_files = []

        for pkg in selected:
            src_path = Path(pkg['location']) / pkg['filename']
            for backup_dir in config['backupDirs']:
                dst_path = Path(backup_dir) / pkg['filename']
                try:
                    if file_operations.copy_file(str(src_path), str(dst_path)):
                        success_count += 1
                        log.info(f"已备份文件: {src_path} -> {dst_path}")
                    else:
                        failed_files.append(str(src_path))
                except Exception as e:
                    log.error(f"备份文件 {src_path} 失败: {str(e)}")
                    failed_files.append(str(src_path))

        # 显示操作结果
        result_msg = f"成功备份了 {success_count}/{len(selected)} 个文件"
        if failed_files:
            result_msg += f"\n\n备份失败的文件:\n" + "\n".join(failed_files[:5])
            if len(failed_files) > 5:
                result_msg += f"\n...等共 {len(failed_files)} 个文件"

        QMessageBox.information(self, "完成", result_msg)
        log.info(f"备份操作结果: {result_msg}")

    def clean_system_cache(self):
        """清理系统缓存"""
        confirm = QMessageBox.question(
            self, "确认清理",
            "确定要清理系统缓存吗？此操作将删除所有未安装软件包的缓存文件",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm != QMessageBox.StandardButton.Yes:
            return
            
        process = QProcess()
        # 使用bash管道自动输入4次y确认
        process.setProgram("bash")
        process.setArguments(["-c", "printf 'y\\n\\ny\\n\\n' | pkexec paru -Scc"])
        
        def handle_output():
            output = process.readAllStandardOutput().data().decode()
            log.info(f"清理输出: {output}")
            
        def handle_error():
            error = process.readAllStandardError().data().decode()
            # 过滤掉交互提示文本
            if not error.strip().startswith("::"):
                log.error(f"清理错误: {error}")
            
        def handle_finished(exit_code, exit_status):
            if exit_code == 0:
                QMessageBox.information(self, "完成", "系统缓存清理成功")
                log.success("系统缓存清理成功")
            else:
                QMessageBox.warning(self, "警告", f"缓存清理失败 (退出码: {exit_code})")
                log.warning(f"缓存清理失败 (退出码: {exit_code})")
        
        process.readyReadStandardOutput.connect(handle_output)
        process.readyReadStandardError.connect(handle_error)
        process.finished.connect(handle_finished)
        
        process.start()