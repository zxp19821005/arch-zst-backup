#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from pathlib import Path
from typing import List, Dict, Optional
from .logger import log
from .package_parser import package_parser

class DirectoryScanner:
    """扫描目录中的软件包文件"""
    
    @staticmethod
    def scan_directory(directory: str, recursive: bool = False) -> List[Dict]:
        """
        扫描指定目录中的软件包文件
        :param directory: 要扫描的目录路径
        :param recursive: 是否递归扫描子目录
        :return: 包含软件包信息的字典列表
        """
        if not os.path.isdir(directory):
            log.error(f"目录不存在或不可访问: {directory}")
            return []
        
        log.info(f"开始扫描目录: {directory} (递归: {recursive})")
        
        package_files = []
        try:
            if recursive:
                for root, _, files in os.walk(directory):
                    for file in files:
                        if file.endswith('.pkg.tar.zst'):
                            full_path = os.path.join(root, file)
                            package_info = package_parser.parse_filename(full_path)
                            if package_info:
                                package_files.append(package_info)
            else:
                for entry in os.scandir(directory):
                    if entry.is_file() and entry.name.endswith('.pkg.tar.zst'):
                        package_info = package_parser.parse_filename(entry.path)
                        if package_info:
                            package_files.append(package_info)
            
            log.success(f"在 {directory} 中找到 {len(package_files)} 个软件包")
            return package_files
        except PermissionError:
            log.error(f"没有权限访问目录: {directory}")
            return []
        except Exception as e:
            log.error(f"扫描目录 {directory} 时出错: {str(e)}")
            return []

# 创建全局扫描器实例
directory_scanner = DirectoryScanner()