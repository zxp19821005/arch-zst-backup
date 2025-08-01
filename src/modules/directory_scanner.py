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
        # 展开路径中的 ~ 符号
        expanded_directory = os.path.expanduser(directory)
        if not os.path.isdir(expanded_directory):
            log.error(f"目录不存在或不可访问: {directory}")
            return []
        
        log.info(f"开始扫描目录: {expanded_directory} (递归: {recursive})")
        
        package_files = []
        try:
            if recursive:
                for root, _, files in os.walk(expanded_directory):
                    for file in files:
                        if file.endswith('.pkg.tar.zst'):
                            full_path = os.path.join(root, file)
                            package_info = package_parser.parse_filename(full_path)
                            if package_info:
                                # 添加文件名信息
                                package_info['filename'] = file
                                # 添加完整路径信息
                                package_info['fullpath'] = full_path
                                # 添加位置信息（只包含子目录名称）
                                relative_path = os.path.relpath(root, expanded_directory)
                                package_info['location'] = relative_path if relative_path != '.' else ''
                                package_files.append(package_info)
            else:
                for entry in os.scandir(expanded_directory):
                    if entry.is_file() and entry.name.endswith('.pkg.tar.zst'):
                        package_info = package_parser.parse_filename(entry.path)
                        if package_info:
                            # 添加文件名信息
                            package_info['filename'] = entry.name
                            # 添加完整路径信息
                            package_info['fullpath'] = entry.path
                            # 添加位置信息（非递归模式下为空）
                            package_info['location'] = ''
                            package_files.append(package_info)
            
            log.success(f"在 {expanded_directory} 中找到 {len(package_files)} 个软件包")
            return package_files
        except PermissionError:
            log.error(f"没有权限访问目录: {expanded_directory}")
            return []
        except Exception as e:
            log.error(f"扫描目录 {expanded_directory} 时出错: {str(e)}")
            return []

# 创建全局扫描器实例
directory_scanner = DirectoryScanner()