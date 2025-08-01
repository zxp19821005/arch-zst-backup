#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import os
from typing import Dict, Optional
from pathlib import Path
from .logger import log

class PackageParser:
    """解析Arch Linux软件包文件名"""

    @staticmethod
    def parse_filename(filename: str) -> Optional[Dict]:
        """
        解析软件包文件名，返回包含各部分的字典
        格式: pkgname-epoch:pkgver-pkgrel-arch.pkg.tar.zst
        改进版：处理路径、特殊后缀和pkgrel格式
        """
        if not filename.endswith('.pkg.tar.zst'):
            log.error(f"无效的文件名格式: {filename}")
            return None

        # 获取纯文件名并移除扩展名
        base_name = os.path.basename(filename)[:-12]
        log.debug(f"解析文件名: {base_name}")

        # 分割所有部分
        parts = base_name.split('-')

        # 必须至少有4部分: pkgname, version, pkgrel, arch
        if len(parts) < 4:
            log.error(f"文件名部分不足: {filename}")
            return None

        # 从后往前获取各部分
        arch = parts[-1]
        pkgrel = parts[-2]

        # 验证pkgrel格式 (允许数字和数字.数字)
        if not re.match(r'^\d+(\.\d+)?$', pkgrel):
            log.error(f"无效的pkgrel格式: {pkgrel}")
            return None

        # 处理包名和版本部分
        remaining_parts = parts[:-2]
        pkgname_parts = []
        version_parts = []

        # 查找版本号开始位置（第一个看起来像版本的部分）
        version_start = len(remaining_parts)  # 默认为最后，表示没有找到版本部分
        for i, part in enumerate(remaining_parts):
            if re.match(r'^\d', part) or ':' in part:
                version_start = i
                break
            pkgname_parts.append(part)

        # 如果没有找到版本部分，尝试从最后两部分提取版本和架构
        if version_start == len(remaining_parts):
            if len(remaining_parts) >= 2:
                # 最后两部分可能是版本和架构
                pkgname_parts = remaining_parts[:-2]
                version_part = remaining_parts[-2]
                # 重新检查架构部分是否有效
                if not re.match(r'^[a-z0-9_]+$', arch):
                    # 如果架构无效，尝试将最后三部分作为版本
                    if len(remaining_parts) >= 3:
                        pkgname_parts = remaining_parts[:-3]
                        version_part = '-'.join(remaining_parts[-3:-1])
                        arch = remaining_parts[-1]
            else:
                # 不足两部分，无法解析
                log.error(f"无法解析软件包名称和版本: {filename}")
                return None
        else:
            version_parts = remaining_parts[version_start:]
            version_part = '-'.join(version_parts)

        # 组合包名和版本部分
        pkgname = '-'.join(pkgname_parts) if pkgname_parts else "unknown"

        # 如果包名为空或仅包含特殊字符，尝试从文件名中提取
        if not pkgname or re.match(r'^[^a-zA-Z0-9]*$', pkgname):
            # 尝试从文件名中提取可能的包名
            name_match = re.search(r'^([a-zA-Z0-9][a-zA-Z0-9+._-]*)', base_name)
            if name_match:
                pkgname = name_match.group(1)
            else:
                log.error(f"无法确定软件包名称: {filename}")
                return None

        # 处理epoch
        epoch = '0'
        if ':' in version_part:
            epoch, pkgver = version_part.split(':', 1)
        else:
            pkgver = version_part

        log.debug(f"包名: {pkgname}, 版本: {pkgver}, epoch: {epoch}, pkgrel: {pkgrel}, 架构: {arch}")

        # 从完整路径中提取目录
        full_path = Path(filename)
        location = str(full_path.parent)

        return {
            'pkgname': pkgname,
            'pkgver': pkgver,
            'epoch': epoch,
            'relver': pkgrel,
            'arch': arch,
            'location': location,
            'filename': filename
        }

# 创建全局解析器实例
package_parser = PackageParser()
