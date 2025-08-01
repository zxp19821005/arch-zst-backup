#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
软件包服务模块

提供软件包相关的业务逻辑，如扫描、去重等
"""

import json
from pathlib import Path
import os
from PySide6.QtWidgets import QMessageBox
from PySide6.QtCore import QProcess
from modules.logger import log
from modules.config_manager import config_manager
from modules.directory_scanner import directory_scanner
from modules.file_operations import file_operations
from modules.package_parser import package_parser
from modules.version_comparator import version_comparator
from ui.components.button_style import ButtonStyle
from utils.decorators import handle_operation_errors

class PackageService:
    """软件包服务类，处理所有与软件包相关的业务逻辑"""

    def __init__(self, cache_manager):
        """初始化软件包服务

        Args:
            cache_manager: 缓存管理器实例
        """
        self.cache_manager = cache_manager

    @handle_operation_errors
    def scan_cache_dirs(self):
        """扫描缓存目录"""
        # 直接执行扫描，不再检查data_loaded状态
        log.info("开始扫描缓存目录")

        config = config_manager.load_config()
        if not config.get('cacheDirs', []):
            msg_box = QMessageBox(QMessageBox.Warning, "警告", "请先在设置中配置缓存目录")
            ok_btn = msg_box.addButton("确定", QMessageBox.AcceptRole)
            ButtonStyle.apply_warning_style(ok_btn)
            msg_box.exec()
            log.warning("未配置缓存目录，无法扫描")
            return

        self.cache_manager.packages = []
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

                    # 将特定的缓存目录路径替换为对应的别名
                    pacman_cache_path = '/var/cache/pacman/pkg'

                    if location == pacman_cache_path:
                        location = 'system_cache'
                    elif location.startswith(os.path.expanduser('~/.cache/paru/clone')):
                        # 确保路径以 / 结尾，避免部分匹配
                        normalized_paru_path = os.path.expanduser('~/.cache/paru/clone').rstrip('/') + '/'
                        if location.startswith(normalized_paru_path):
                            sub_path = location.replace(normalized_paru_path, '').lstrip('/')
                            location = f'paru_cache/{sub_path}' if sub_path else 'paru_cache'
                    elif location.startswith(os.path.expanduser('~/.cache/yay')):
                        # 确保路径以 / 结尾，避免部分匹配
                        normalized_yay_path = os.path.expanduser('~/.cache/yay').rstrip('/') + '/'
                        if location.startswith(normalized_yay_path):
                            sub_path = location.replace(normalized_yay_path, '').lstrip('/')
                            location = f'yay_cache/{sub_path}' if sub_path else 'yay_cache'
                        location = f'yay缓存{sub_path}'

                    pkg['location'] = location
                    self.cache_manager.packages.append(pkg)

        self.cache_manager.update_table()

        # 计算重复软件包数量和可备份软件包数量
        duplicate_count = self.cache_manager.count_duplicate_packages()
        backupable_count = self.cache_manager.count_backupable_packages()

        # 更新状态栏
        self.cache_manager.update_status_bar()

        # 保存扫描结果
        config_dir = Path(config_manager.config_dir)
        packages_file = config_dir / "updated_packages.json"

        try:
            with open(packages_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache_manager.packages, f, indent=4, ensure_ascii=False)
            log.success(f"保存了 {len(self.cache_manager.packages)} 个软件包到 {packages_file}")
            # 扫描完成
            log.info("缓存目录扫描完成")
        except Exception as e:
            log.error(f"保存软件包列表失败: {str(e)}")
            QMessageBox.critical(self.cache_manager, "错误", "保存软件包列表失败")

    @handle_operation_errors
    def deduplicate_packages(self):
        """去重软件包，保留最新版本"""
        if not self.cache_manager.packages:
            QMessageBox.warning(self.cache_manager, "警告", "请先扫描缓存目录")
            return

        # 按名称分组
        packages_by_name = {}
        for pkg in self.cache_manager.packages:
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
            QMessageBox.information(self.cache_manager, "信息", "没有发现重复的软件包")
            return

        # 显示确认对话框
        confirm = QMessageBox.question(
            self.cache_manager, "确认去重",
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

            from ..pages.common_utils import force_rescan_and_update_status_bar
            force_rescan_and_update_status_bar(self.cache_manager, self.cache_manager.count_duplicate_packages, 
                                             self.cache_manager.count_backupable_packages)

            # 更新状态栏
            self.cache_manager.update_status_bar()

            # 显示操作结果
            result_msg = f"成功删除了 {success_count}/{len(to_delete)} 个旧版本软件包"
            if failed_files:
                result_msg += f"\n\n删除失败的文件:\n" + "\n".join(failed_files[:5])
                if len(failed_files) > 5:
                    result_msg += f"\n...等共 {len(failed_files)} 个文件"

            QMessageBox.information(self.cache_manager, "完成", result_msg)
            log.info(f"去重操作结果: {result_msg}")

    @handle_operation_errors
    def delete_selected(self):
        """删除选中的软件包"""
        selected = self.cache_manager.get_selected_packages()
        if not selected:
            QMessageBox.warning(self.cache_manager, "警告", "请先选择要删除的软件包")
            return

        confirm = QMessageBox.question(
            self.cache_manager, "确认删除",
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

            from ..pages.common_utils import force_rescan_and_update_status_bar
            force_rescan_and_update_status_bar(self.cache_manager, self.cache_manager.count_duplicate_packages, 
                                             self.cache_manager.count_backupable_packages)

            # 更新状态栏
            self.cache_manager.update_status_bar()

            # 显示操作结果
            result_msg = f"成功删除了 {success_count}/{len(selected)} 个软件包"
            if failed_files:
                result_msg += f"\n\n删除失败的文件:\n" + "\n".join(failed_files[:5])
                if len(failed_files) > 5:
                    result_msg += f"\n...等共 {len(failed_files)} 个文件"

            QMessageBox.information(self.cache_manager, "完成", result_msg)
            log.info(f"删除操作结果: {result_msg}")
