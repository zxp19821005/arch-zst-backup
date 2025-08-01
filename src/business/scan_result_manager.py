#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
扫描结果管理功能模块
"""

import logging
import json
from pathlib import Path
from typing import List, Dict

log = logging.getLogger(__name__)


class ScanResultManager:
    """扫描结果管理器，负责处理扫描结果保存和加载相关的业务逻辑"""

    def __init__(self, backup_manager, config_manager):
        """初始化扫描结果管理器

        Args:
            backup_manager: 备份管理器实例
            config_manager: 配置管理器实例
        """
        self.backup_manager = backup_manager
        self.config_manager = config_manager

    def save_scan_results(self) -> None:
        """保存扫描结果到本地文件

        该方法会将当前扫描到的软件包列表保存到配置目录下的
        existing_packages.json文件中。保存前会移除filename字段，
        以避免在不同系统间迁移时出现路径问题。

        Returns:
            None

        Raises:
            PermissionError: 当没有写入权限时
            OSError: 当文件系统出现问题时
            json.JSONEncodeError: 当JSON编码失败时
        """
        config_dir = Path(self.config_manager.config_dir)
        packages_file = config_dir / "existing_packages.json"

        try:
            # 保存前移除 filename 字段
            packages_to_save = []
            for pkg in self.backup_manager.packages:
                pkg_copy = pkg.copy()
                pkg_copy.pop('filename', None)  # 移除 filename 字段
                packages_to_save.append(pkg_copy)

            with open(packages_file, 'w', encoding='utf-8') as f:
                json.dump(packages_to_save, f, indent=4, ensure_ascii=False)
            log.info(f"保存了 {len(self.backup_manager.packages)} 个软件包到 {packages_file}")
            # 扫描完成
            log.info("备份目录扫描完成")
        except (PermissionError, OSError) as e:
            log.error(f"保存软件包列表失败，权限或文件系统错误: {str(e)}")
            log.error(f"尝试写入路径: {packages_file}")
            raise e
        except Exception as e:
            log.error(f"保存软件包列表时发生未知错误: {str(e)}")
            raise e

    def load_scan_results(self) -> List[Dict]:
        """从本地文件加载扫描结果

        该方法会尝试从配置目录下的existing_packages.json文件中
        加载之前保存的软件包列表。

        Returns:
            List[Dict]: 加载的软件包列表，如果文件不存在或加载失败则返回空列表

        Raises:
            PermissionError: 当没有读取权限时
            OSError: 当文件系统出现问题时
            json.JSONDecodeError: 当JSON解码失败时
        """
        config_dir = Path(self.config_manager.config_dir)
        packages_file = config_dir / "existing_packages.json"

        try:
            if not packages_file.exists():
                log.info("未找到扫描结果文件")
                return []

            with open(packages_file, 'r', encoding='utf-8') as f:
                packages = json.load(f)

            log.info(f"从 {packages_file} 加载了 {len(packages)} 个软件包")
            return packages

        except (PermissionError, OSError) as e:
            log.error(f"加载软件包列表失败，权限或文件系统错误: {str(e)}")
            log.error(f"尝试读取路径: {packages_file}")
            raise e
        except json.JSONDecodeError as e:
            log.error(f"加载软件包列表失败，JSON解码错误: {str(e)}")
            raise e
        except Exception as e:
            log.error(f"加载软件包列表时发生未知错误: {str(e)}")
            raise e
