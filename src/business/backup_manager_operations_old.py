#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
备份管理器操作类，负责处理所有业务逻辑
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from functools import wraps

from modules.logger import log
from modules.config_manager import config_manager
from modules.directory_scanner import directory_scanner
from modules.version_comparator import version_comparator
from utils.common_utils import count_duplicate_packages
from utils.decorators import handle_errors
from .package_deduplicator import PackageDeduplicator
from .package_deleter import PackageDeleter
from .ui_handler import UIHandler
from .scan_result_manager import ScanResultManager


class BackupManagerOperations:
    """备份管理器操作类，负责处理所有业务逻辑"""

    def __init__(self, backup_manager: 'BackupManagerPage') -> None:
        """初始化操作类

        Args:
            backup_manager: 父级BackupManagerPage实例
        """
        self.backup_manager = backup_manager

        # 初始化辅助模块
        self.package_deduplicator = PackageDeduplicator(version_comparator)
        self.package_deleter = PackageDeleter(self)
        self.ui_handler = UIHandler(backup_manager)
        self.scan_result_manager = ScanResultManager(backup_manager, config_manager)

    @handle_errors
    def scan_backup_dir(self) -> None:
        """扫描备份目录中的软件包

        该方法会从配置中获取备份目录路径，检查目录是否存在和可读，
        然后使用目录扫描器扫描所有软件包，并更新界面显示。
        扫描完成后会计算并显示重复软件包的数量。

        Returns:
            None

        Raises:
            FileNotFoundError: 当备份目录不存在时
            PermissionError: 当备份目录不可读时
        """
        log.info("开始扫描备份目录")

        config = config_manager.load_config()
        if not config.get('backupDir'):
            self.ui_handler.show_warning("请先在设置中配置备份目录")
            log.warning("未配置备份目录，无法扫描")
            return

        backup_dir = config['backupDir']
        log.info(f"扫描备份目录: {backup_dir}")

        # 检查目录是否存在
        if not Path(backup_dir).exists():
            self.ui_handler.show_error(f"备份目录不存在: {backup_dir}")
            log.error(f"备份目录不存在: {backup_dir}")
            return

        # 检查目录是否可读
        if not os.access(backup_dir, os.R_OK):
            self.ui_handler.show_error(f"备份目录无法读取，请检查权限: {backup_dir}")
            log.error(f"备份目录无法读取: {backup_dir}")
            return

        try:
            # 扫描目录，添加重试机制
            max_retries = 2
            for attempt in range(max_retries + 1):
                try:
                    self.backup_manager.packages = directory_scanner.scan_directory(backup_dir, recursive=True)
                    break
                except (PermissionError, OSError) as e:
                    if attempt < max_retries:
                        log.warning(f"扫描目录失败，尝试重试 ({attempt + 1}/{max_retries}): {str(e)}")
                        import time
                        time.sleep(1)  # 等待1秒后重试
                    else:
                        raise e

            self.backup_manager.update_table()
        except (PermissionError, OSError) as e:
            log.error(f"扫描备份目录失败: {str(e)}")
            self.ui_handler.show_error(f"扫描备份目录失败: {str(e)}")
            return
        except Exception as e:
            log.error(f"扫描备份目录时发生未知错误: {str(e)}")
            log.error(f"错误类型: {type(e).__name__}")
            self.ui_handler.show_error("扫描备份目录失败: 未知错误")
            return

        # 计算重复软件包数量
        duplicate_count = self.backup_manager.count_duplicate_packages()

        # 在状态栏显示软件包统计信息
        self.ui_handler.update_status_bar_with_message(
            f"共 {len(self.backup_manager.packages)} 个软件包，其中有 {duplicate_count} 个重复软件包",
            "没有找到软件包，请检查备份目录配置"
        )

        # 保存扫描结果
        self.scan_result_manager.save_scan_results()

    @handle_errors
    def deduplicate_packages(self) -> None:
        """去重软件包，保留每个软件包的最新版本

        该方法会按软件包名称和架构分组，然后比较同一组内软件包的版本号，
        保留最新版本，将旧版本添加到删除列表。

        Returns:
            None

        Raises:
            RuntimeError: 当没有可处理的软件包时
        """
        if not self.backup_manager.packages:
            self.ui_handler.show_warning("没有可处理的软件包，请先扫描备份目录")
            return

        log.info(f"开始去重处理，共有 {len(self.backup_manager.packages)} 个软件包")

        # 按名称和架构分组软件包
        grouped, skipped_count = self.package_deduplicator.group_packages_by_name_and_arch(self.backup_manager.packages)
        log.info(f"软件包分组完成，共有 {len(grouped)} 个组，跳过了 {skipped_count} 个软件包")

        # 找出需要删除的旧版本
        to_delete = self.package_deduplicator.find_packages_to_delete(grouped)

        if not to_delete:
            self.ui_handler.show_info("没有找到可去重的软件包")
            log.info("没有找到需要删除的软件包，可能所有软件包都是最新版本")
            return

        log.info(f"找到 {len(to_delete)} 个需要删除的旧版本软件包")

        # 确认并删除软件包
        success_count, failed_files = self.package_deleter.confirm_and_delete_packages(to_delete)

        # 如果用户取消了操作，直接返回
        if success_count == 0 and not failed_files:
            return

        # 强制重新扫描并更新状态栏
        log.info("开始重新扫描目录以更新列表")
        self._update_status_bar_after_operation()

        # 生成并显示结果消息
        result_msg = self.package_deleter.generate_result_message(to_delete, success_count, failed_files)
        self.ui_handler.show_info(result_msg)
        log.info(f"去重操作结果: {result_msg}")

    @handle_errors
    def delete_selected(self) -> None:
        """删除选中的软件包

        该方法会获取用户在界面中选中的软件包，
        显示确认对话框，并在用户确认后执行删除操作。

        Returns:
            None

        Raises:
            RuntimeError: 当没有选中的软件包时
        """
        selected = self.backup_manager.get_selected_packages()
        if not selected:
            self.ui_handler.show_warning("请先选择要删除的软件包")
            return

        confirm = self.ui_handler.show_confirmation(
            f"确定要删除选中的 {len(selected)} 个软件包吗？此操作不可撤销！",
            packages=selected
        )
        if not confirm:
            return

        # 执行删除
        success_count, _ = self.package_deleter.execute_deletion(selected)

        # 强制重新加载列表并更新状态栏
        self._update_status_bar_after_operation()

        self.ui_handler.show_info(f"成功删除了 {success_count}/{len(selected)} 个软件包")
        log.info(f"删除了 {success_count}/{len(selected)} 个选中的软件包")

        # 状态栏更新已在 _update_status_bar_after_operation 中处理

    def _update_status_bar_after_operation(self) -> None:
        """在操作后更新状态栏"""
        # 重新扫描目录
        self.scan_backup_dir()

        # 更新状态栏
        if self.backup_manager.packages:
            duplicate_count = self.backup_manager.count_duplicate_packages()
            message = f"共 {len(self.backup_manager.packages)} 个软件包，其中有 {duplicate_count} 个重复软件包"
        else:
            message = "没有找到软件包，请检查备份目录配置"

        self.ui_handler.update_status_bar_with_message(message, message)