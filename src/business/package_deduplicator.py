#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
软件包去重功能模块
"""

import logging
from typing import List, Dict, Tuple, Optional

log = logging.getLogger(__name__)


class PackageDeduplicator:
    """软件包去重器，负责处理软件包去重相关的业务逻辑"""

    def __init__(self, version_comparator):
        """初始化去重器

        Args:
            version_comparator: 版本比较器实例
        """
        self.version_comparator = version_comparator

    def group_packages_by_name_and_arch(self, packages: List[Dict]) -> Tuple[Dict, int]:
        """按名称和架构分组软件包

        Args:
            packages (List[Dict]): 软件包列表

        Returns:
            Tuple[Dict, int]: (分组字典, 跳过的软件包数量)
        """
        grouped = {}
        skipped_count = 0

        for pkg in packages:
            # 确保必要的字段存在，支持不同的字段名
            pkg_name = pkg.get('pkgname') or pkg.get('name')
            pkg_arch = pkg.get('arch')

            if not pkg_name or not pkg_arch:
                log.warning(f"跳过格式不正确的软件包: {pkg}")
                skipped_count += 1
                continue

            key = (pkg_name, pkg_arch)
            grouped.setdefault(key, []).append(pkg)

        return grouped, skipped_count

    def find_latest_package(self, packages: List[Dict]) -> Optional[Dict]:
        """在一组软件包中找出最新版本

        Args:
            packages (List[Dict]): 软件包列表

        Returns:
            Optional[Dict]: 最新版本的软件包，如果没有有效的软件包则返回None
        """
        if not packages:
            return None

        # 确保所有软件包都有必要的版本字段
        valid_pkgs = []
        for pkg in packages:
            # 确保版本字段存在，支持不同的字段名
            pkg_version = pkg.get('pkgver') or pkg.get('version')
            pkg_rel = pkg.get('relver') or pkg.get('pkgrel')
            pkg_epoch = pkg.get('epoch') or '0'
            name = pkg.get('pkgname') or pkg.get('name')
            arch = pkg.get('arch')

            if not pkg_version or not pkg_rel:
                log.warning(f"软件包 {name} 缺少版本信息，跳过")
                continue

            # 创建标准化的软件包对象用于版本比较
            pkg_for_compare = {
                'pkgname': name,
                'pkgver': pkg_version,
                'relver': pkg_rel,
                'epoch': pkg_epoch,
                'arch': arch
            }

            # 保存原始包和标准化对象
            valid_pkgs.append({
                'original': pkg,
                'compare_obj': pkg_for_compare
            })

        if not valid_pkgs:
            return None

        # 找出最新版本
        latest = valid_pkgs[0]
        log.debug(f"初始最新版本: {latest['compare_obj']['pkgname']}-{latest['compare_obj']['pkgver']}-{latest['compare_obj']['relver']}")

        for pkg in valid_pkgs[1:]:
            comparison_result = self.version_comparator.compare_versions(pkg['compare_obj'], latest['compare_obj'])
            log.debug(f"比较版本: {pkg['compare_obj']['pkgname']}-{pkg['compare_obj']['pkgver']}-{pkg['compare_obj']['relver']} vs {latest['compare_obj']['pkgname']}-{latest['compare_obj']['pkgver']}-{latest['compare_obj']['relver']} = {comparison_result}")

            if comparison_result > 0:
                latest = pkg
                log.debug(f"更新最新版本为: {latest['compare_obj']['pkgname']}-{latest['compare_obj']['pkgver']}-{latest['compare_obj']['relver']}")

        return latest['original']

    def find_packages_to_delete(self, grouped: Dict) -> List[Dict]:
        """找出需要删除的旧版本软件包

        Args:
            grouped (Dict): 按名称和架构分组的软件包字典

        Returns:
            List[Dict]: 需要删除的软件包列表
        """
        to_delete = []

        for (name, arch), pkgs in grouped.items():
            if len(pkgs) > 1:
                try:
                    # 找出最新版本
                    latest = self.find_latest_package(pkgs)

                    if latest is None:
                        log.warning(f"软件包组 {name} 没有有效的版本信息，跳过")
                        continue

                    log.info(f"软件包组 {name} ({arch}) 的最新版本: {latest.get('pkgver') or latest.get('version')}-{latest.get('relver') or latest.get('pkgrel')}")

                    # 将非最新版本的软件包添加到删除列表
                    delete_count = 0
                    for pkg in pkgs:
                        if pkg != latest:
                            to_delete.append(pkg)
                            delete_count += 1
                            log.debug(f"标记删除: {pkg.get('filename', '')}")

                    log.info(f"软件包组 {name} ({arch}) 将删除 {delete_count} 个旧版本")
                except Exception as e:
                    log.error(f"比较软件包 {name} 版本时出错: {str(e)}")
                    continue

        return to_delete
