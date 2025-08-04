#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
from typing import Dict, List, Optional
from src.modules.package_parser import PackageParser, package_parser
from src.modules.logger import log

class VersionComparator:
    """比较Arch Linux软件包版本"""
    
    @staticmethod
    def compare_versions(pkg1: Dict, pkg2: Dict) -> int:
        """
        比较两个软件包版本
        返回: 
          -1: pkg1 < pkg2
          0: pkg1 == pkg2
          1: pkg1 > pkg2
        """
        # 比较epoch
        if pkg1['epoch'] != pkg2['epoch']:
            return 1 if pkg1['epoch'] > pkg2['epoch'] else -1
        
        # 比较主版本号
        ver1 = pkg1['pkgver'].split('.')
        ver2 = pkg2['pkgver'].split('.')
        
        for v1, v2 in zip(ver1, ver2):
            if v1 != v2:
                # 尝试转换为数字比较
                if v1.isdigit() and v2.isdigit():
                    return 1 if int(v1) > int(v2) else -1
                # 否则按字符串比较
                return 1 if v1 > v2 else -1
        
        # 如果主版本号相同但长度不同
        if len(ver1) != len(ver2):
            return 1 if len(ver1) > len(ver2) else -1
        
        # 比较pkgrel
        rel1 = pkg1['relver'].split('.')
        rel2 = pkg2['relver'].split('.')
        
        for r1, r2 in zip(rel1, rel2):
            if r1 != r2:
                if r1.isdigit() and r2.isdigit():
                    return 1 if int(r1) > int(r2) else -1
                return 1 if r1 > r2 else -1
        
        # 如果relver长度不同
        if len(rel1) != len(rel2):
            return 1 if len(rel1) > len(rel2) else -1
        
        # 完全相等
        return 0
    
    @staticmethod
    def find_latest(packages: List[Dict]) -> Optional[Dict]:
        """
        从一组软件包中找出最新版本
        返回最新版本的软件包信息字典
        """
        if not packages:
            log.error("空软件包列表")
            return None
            
        latest = packages[0]
        
        for pkg in packages[1:]:
            if VersionComparator.compare_versions(pkg, latest) > 0:
                latest = pkg
                
        return latest
    
    @staticmethod
    def find_latest_from_filenames(filenames: List[str]) -> Optional[Dict]:
        """
        从一组文件名中找出最新版本的软件包
        返回最新版本的软件包信息字典
        """
        packages = []
        
        for filename in filenames:
            pkg_info = package_parser.parse_filename(filename)
            if pkg_info:
                packages.append(pkg_info)
        
        if not packages:
            log.error("没有有效的软件包可以比较")
            return None
            
        return VersionComparator.find_latest(packages)

# 创建全局比较器实例
version_comparator = VersionComparator()