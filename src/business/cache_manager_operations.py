#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from pathlib import Path
import os
from PySide6.QtWidgets import QMessageBox, QInputDialog
from PySide6.QtCore import QProcess
from modules.logger import log
from modules.config_manager import config_manager
from modules.directory_scanner import directory_scanner
from modules.file_operations import file_operations
from modules.package_parser import package_parser
from modules.version_comparator import version_comparator
from ui.components.button_style import ButtonStyle
from utils.common_utils import force_rescan_and_update_status_bar

class CacheManagerOperations:
    """缓存管理器操作类，负责处理所有业务逻辑"""

    def __init__(self, cache_manager):
        """初始化操作类

        Args:
            cache_manager: 父级CacheManagerPage实例
        """
        self.cache_manager = cache_manager

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

    def deduplicate_packages(self):
        """去重软件包，保留最新版本"""
        if not self.cache_manager.packages:
            QMessageBox.warning(self.cache_manager, "警告", "请先扫描缓存目录")
            return

        # 按名称分组
        packages_by_name = {}
        for pkg in self.cache_manager.packages:
            # 确保必要的字段存在
            pkg_name = pkg.get('pkgname')
            if not pkg_name:
                log.warning(f"跳过没有名称的软件包: {pkg}")
                continue

            if pkg_name not in packages_by_name:
                packages_by_name[pkg_name] = []
            packages_by_name[pkg_name].append(pkg)

        # 找出需要删除的旧版本
        to_delete = []
        for name, pkgs in packages_by_name.items():
            if len(pkgs) > 1:
                try:
                    # 确保所有软件包都有必要的版本字段
                    valid_pkgs = []
                    for pkg in pkgs:
                        # 确保版本字段存在
                        pkg_version = pkg.get('pkgver')
                        pkg_rel = pkg.get('relver')
                        pkg_epoch = pkg.get('epoch') or '0'
                        pkg_arch = pkg.get('arch')

                        if not pkg_version or not pkg_rel or not pkg_arch:
                            log.warning(f"软件包 {name} 缺少版本或架构信息，跳过")
                            continue

                        # 创建标准化的软件包对象用于版本比较
                        pkg_for_compare = {
                            'pkgname': name,
                            'pkgver': pkg_version,
                            'relver': pkg_rel,
                            'epoch': pkg_epoch,
                            'arch': pkg_arch
                        }

                        # 保存原始包和标准化对象
                        valid_pkgs.append({
                            'original': pkg,
                            'compare_obj': pkg_for_compare
                        })

                    if not valid_pkgs:
                        log.warning(f"软件包组 {name} 没有有效的版本信息，跳过")
                        continue

                    # 找出最新版本
                    latest = valid_pkgs[0]
                    for pkg in valid_pkgs[1:]:
                        if version_comparator.compare_versions(pkg['compare_obj'], latest['compare_obj']) > 0:
                            latest = pkg

                    # 将非最新版本的软件包添加到删除列表
                    for pkg in valid_pkgs:
                        if pkg != latest:
                            to_delete.append(pkg['original'])

                    log.debug(f"软件包 {name} 保留版本: {latest['compare_obj']['pkgver']}-{latest['compare_obj']['relver']}")
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

            # 执行刷新操作，确保列表更新
            log.info("执行刷新操作，更新软件包列表")
            if hasattr(self.cache_manager, 'scan_button'):
                # 模拟点击扫描按钮
                self.cache_manager.scan_button.click()
            elif hasattr(self.cache_manager, 'scan_cache_dirs'):
                # 直接调用扫描方法
                self.cache_manager.scan_cache_dirs()

    def check_for_updates(self):
        """检查系统更新"""
        log.info("开始检查系统更新")
        try:
            self.cache_manager.process = QProcess()
            self.cache_manager.process.finished.connect(lambda: self.cache_manager.on_update_finished())
            self.cache_manager.process.errorOccurred.connect(self.cache_manager.on_update_error)

            # 调用终端执行命令
            command = "xterm"
            args = ["-e", "bash", "-c", "paru; read -p '按回车键退出...'"]
            log.debug(f"执行命令: {command} {args}")
            self.cache_manager.process.start(command, args)

            if not self.cache_manager.process.waitForStarted(5000):
                log.error("启动更新检查进程失败")
                QMessageBox.critical(self.cache_manager, "错误", "无法启动更新检查进程")
        except Exception as e:
            log.error(f"检查更新时发生错误: {str(e)}")
            QMessageBox.critical(self.cache_manager, "错误", f"检查更新失败: {str(e)}")
