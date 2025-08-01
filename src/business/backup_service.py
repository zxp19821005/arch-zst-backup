#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
备份服务模块

提供软件包备份相关的业务逻辑
"""

import json
from pathlib import Path
from PySide6.QtWidgets import QMessageBox, QInputDialog
from modules.logger import log
from modules.config_manager import config_manager
from modules.file_operations import file_operations
from modules.version_comparator import version_comparator
from utils.decorators import handle_operation_errors

class BackupService:
    """备份服务类，处理所有与备份相关的业务逻辑"""

    def __init__(self, cache_manager):
        """初始化备份服务

        Args:
            cache_manager: 缓存管理器实例
        """
        self.cache_manager = cache_manager

    @handle_operation_errors
    def backup_newer_versions(self):
        """备份较新版本的软件包"""
        try:
            log.debug("开始备份新版本软件包")

            config_dir = Path(config_manager.config_dir)
            updated_packages_file = config_dir / "updated_packages.json"
            existing_packages_file = config_dir / "existing_packages.json"

            # 检查JSON文件是否存在
            if not updated_packages_file.exists() or not existing_packages_file.exists():
                QMessageBox.warning(self.cache_manager, "警告", "缺少必要的JSON文件")
                return

            # 读取更新的软件包列表
            with open(updated_packages_file, 'r', encoding='utf-8') as f:
                updated_packages = json.load(f)
                if not isinstance(updated_packages, list):
                    QMessageBox.critical(self.cache_manager, "错误", "updated_packages.json 格式错误：应为列表")
                    return

                # 检查每个软件包的格式
                for pkg in updated_packages:
                    if not isinstance(pkg, dict):
                        QMessageBox.critical(self.cache_manager, "错误", f"updated_packages.json 条目格式错误：{type(pkg)}")
                        return

            # 读取现有的软件包列表
            with open(existing_packages_file, 'r', encoding='utf-8') as f:
                existing_packages = json.load(f)
                if not isinstance(existing_packages, list):
                    QMessageBox.critical(self.cache_manager, "错误", "existing_packages.json 格式错误：应为列表")
                    return

                # 检查每个软件包的格式
                for pkg in existing_packages:
                    if not isinstance(pkg, dict):
                        QMessageBox.critical(self.cache_manager, "错误", f"existing_packages.json 条目格式错误：{type(pkg)}")
                        return

            # 获取备份目录
            config = config_manager.load_config()
            base_backup_dir = Path(config.get('backupDir', '/path/to/backup'))
            if not base_backup_dir.exists():
                QMessageBox.critical(self.cache_manager, "错误", "备份目录不存在")
                return
            backup_dir = base_backup_dir
            if not backup_dir.exists():
                backup_dir.mkdir(parents=True, exist_ok=True)

            success_count = 0
            # 用于记录已经处理过的软件包，避免重复备份
            processed_packages = set()

            for pkg in updated_packages:
                if not isinstance(pkg, dict):
                    log.error(f"包数据格式错误: {type(pkg)}")
                    continue

                pkg_name = pkg.get('pkgname')
                if not isinstance(pkg_name, str):
                    log.error(f"包名称格式错误: {type(pkg_name)}")
                    continue

                # 检查是否已经处理过这个软件包
                if pkg_name in processed_packages:
                    log.debug(f"跳过已处理的软件包: {pkg_name}")
                    continue

                processed_packages.add(pkg_name)

                # 查找匹配的现有软件包，支持不同的字段名
                existing_pkg = None
                for ep in existing_packages:
                    if not isinstance(ep, dict):
                        continue

                    # 尝试不同的字段名
                    ep_name = ep.get('pkgname') or ep.get('name')
                    if ep_name == pkg_name:
                        existing_pkg = ep
                        break

                if not existing_pkg or not isinstance(existing_pkg, dict):
                    log.info(f"未找到匹配的包或格式错误: {pkg_name}")
                    continue

                # 确保版本字段存在，支持不同的字段名
                pkg_version = pkg.get('pkgver') or pkg.get('version')
                existing_version = existing_pkg.get('pkgver') or existing_pkg.get('version')

                if not pkg_version or not existing_version:
                    log.error(f"包 {pkg_name} 缺少版本字段")
                    continue

                # 确保发布版本字段存在，支持不同的字段名
                pkg_rel = pkg.get('relver') or pkg.get('pkgrel')
                existing_rel = existing_pkg.get('relver') or existing_pkg.get('pkgrel')

                if not pkg_rel or not existing_rel:
                    log.error(f"包 {pkg_name} 缺少发布版本字段")
                    continue

                # 确保epoch字段存在，支持不同的字段名
                pkg_epoch = pkg.get('epoch') or '0'
                existing_epoch = existing_pkg.get('epoch') or '0'

                # 创建标准化的软件包对象用于版本比较
                pkg_for_compare = {
                    'pkgname': pkg_name,
                    'pkgver': pkg_version,
                    'relver': pkg_rel,
                    'epoch': pkg_epoch
                }

                existing_for_compare = {
                    'pkgname': pkg_name,
                    'pkgver': existing_version,
                    'relver': existing_rel,
                    'epoch': existing_epoch
                }

                # 比较版本，只备份较新版本
                comparison_result = version_comparator.compare_versions(pkg_for_compare, existing_for_compare)
                log.debug(f"软件包 {pkg_name} 版本比较: {pkg_version}-{pkg_rel} vs {existing_version}-{existing_rel} = {comparison_result}")

                if comparison_result > 0:
                    if 'fullpath' not in pkg or 'filename' not in pkg:
                        log.error(f"包 {pkg_name} 缺少 fullpath 或 filename 字段")
                        continue

                    src_path = Path(pkg['fullpath'])
                    if not src_path.exists():
                        log.error(f"源文件不存在: {src_path}")
                        continue

                    # 使用existing_packages中的location字段作为子目录
                    # 首先尝试从existing_pkg中获取location
                    location = existing_pkg.get('location', '')
                    # 如果existing_pkg中没有location，则尝试从pkg中获取
                    if not location:
                        location = pkg.get('location', '')

                    if location:
                        # 如果location是绝对路径，则转换为相对于备份目录的路径
                        location_path = Path(location)
                        if location_path.is_absolute():
                            # 尝试找到相对于备份目录的路径
                            try:
                                relative_path = location_path.relative_to(backup_dir)
                                location = str(relative_path)
                            except ValueError:
                                # 如果无法计算相对路径，则使用路径的最后一部分
                                location = location_path.name

                        location = location.strip().replace(' ', '-')
                        location_dir = backup_dir / location
                        location_dir.mkdir(parents=True, exist_ok=True)
                        dest_path = location_dir / pkg['filename']
                    else:
                        dest_path = backup_dir / pkg['filename']
                    # 检查目标文件是否已存在
                    if dest_path.exists():
                        log.debug(f"目标文件已存在，跳过: {dest_path}")
                        continue

                    try:
                        if file_operations.copy_file(str(src_path), str(dest_path)):
                            success_count += 1
                            log.info(f"成功备份新版本: {pkg_name} ({pkg['pkgver']}-{pkg.get('relver', '')}) -> {dest_path}")
                        else:
                            log.error(f"备份失败: {src_path} -> {dest_path}")
                    except Exception as e:
                        log.error(f"文件拷贝时发生错误: {str(e)}")
                else:
                    log.debug(f"软件包 {pkg_name} 版本不是新版本，跳过备份")

            QMessageBox.information(self.cache_manager, "完成", f"成功备份了 {success_count} 个较新版本的软件包")
            log.debug("备份新版本软件包完成")
        except Exception as e:
            log.error(f"备份新版本软件包失败: {str(e)}")
            QMessageBox.critical(self.cache_manager, "错误", f"备份失败: {str(e)}")

    @handle_operation_errors
    def backup_to_subdirectory(self):
        """备份到子目录"""
        try:
            log.debug("开始备份到子目录")
            config = config_manager.load_config()
            backup_dir = Path(config.get('backupDir', '/path/to/backup'))
            if not backup_dir.exists():
                QMessageBox.critical(self.cache_manager, "错误", "备份目录不存在")
                return

            selected = self.cache_manager.get_selected_packages()
            if not selected:
                QMessageBox.warning(self.cache_manager, "警告", "请先选择要备份的软件包")
                return

            # 获取所有子目录
            subdirs = [d for d in backup_dir.iterdir() if d.is_dir()]

            # 如果没有子目录，显示警告
            if not subdirs:
                QMessageBox.warning(self.cache_manager, "警告", "备份目录中没有子目录")
                return

            # 创建目录选择对话框
            item, ok = QInputDialog.getItem(self.cache_manager, "选择子目录", "请选择一个子目录:",
                                          [d.name for d in subdirs], 0, False)

            if not ok or not item:
                return

            subdir = item

            target_dir = backup_dir / subdir
            if not file_operations.ensure_directory_exists(str(target_dir)):
                QMessageBox.warning(self.cache_manager, "警告", "创建子目录失败")
                return

            success_count = 0
            for pkg in selected:
                src_path = Path(pkg['fullpath'])
                dest_path = target_dir / pkg['filename']
                if file_operations.copy_file(str(src_path), str(dest_path)):
                    success_count += 1

            QMessageBox.information(self.cache_manager, "完成", f"成功备份了 {success_count} 个软件包到 {subdir}")
        except Exception as e:
            log.error(f"备份到子目录失败: {str(e)}")
            QMessageBox.critical(self.cache_manager, "错误", f"备份失败: {str(e)}")

    def _backup_packages(self, packages, target_dir):
        """通用的备份软件包方法

        Args:
            packages: 要备份的软件包列表
            target_dir: 目标目录

        Returns:
            int: 成功备份的软件包数量
        """
        success_count = 0
        for pkg in packages:
            src_path = Path(pkg['fullpath'])
            dest_path = target_dir / pkg['filename']
            if file_operations.copy_file(str(src_path), str(dest_path)):
                success_count += 1
        return success_count
