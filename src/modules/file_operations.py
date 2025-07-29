#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil
from pathlib import Path
from typing import Optional
from .logger import log

class FileOperations:
    """处理文件操作的工具类"""
    
    @staticmethod
    def copy_file(src: str, dest: str) -> bool:
        """
        安全拷贝文件
        :param src: 源文件路径
        :param dest: 目标文件路径
        :return: 是否成功
        """
        try:
            # 检查源文件是否存在
            if not os.path.isfile(src):
                log.error(f"源文件不存在: {src}")
                return False
            
            # 检查目标目录是否存在并可写
            dest_dir = os.path.dirname(dest)
            if not os.path.isdir(dest_dir):
                try:
                    os.makedirs(dest_dir, exist_ok=True)
                    log.info(f"创建目标目录: {dest_dir}")
                except OSError as e:
                    log.error(f"无法创建目标目录 {dest_dir}: {str(e)}")
                    return False
            
            if not os.access(dest_dir, os.W_OK):
                log.error(f"目标目录不可写: {dest_dir}")
                return False
            
            # 执行拷贝
            log.info(f"正在拷贝文件: {src} -> {dest}")
            shutil.copy2(src, dest)
            log.success(f"文件拷贝成功: {src} -> {dest}")
            return True
            
        except PermissionError:
            log.error(f"没有权限拷贝文件: {src}")
            return False
        except Exception as e:
            log.error(f"拷贝文件时出错: {str(e)}")
            return False
    
    @staticmethod
    def delete_file(file_path: str) -> bool:
        """
        安全删除文件
        :param file_path: 要删除的文件路径
        :return: 是否成功
        """
        try:
            # 检查文件是否存在
            if not os.path.isfile(file_path):
                log.error(f"文件不存在: {file_path}")
                return False
            
            # 检查文件是否可写
            if not os.access(file_path, os.W_OK):
                log.error(f"文件不可写: {file_path}")
                return False
            
            # 执行删除
            log.info(f"正在删除文件: {file_path}")
            os.remove(file_path)
            log.success(f"文件删除成功: {file_path}")
            return True
            
        except PermissionError:
            log.error(f"没有权限删除文件: {file_path}")
            return False
        except Exception as e:
            log.error(f"删除文件时出错: {str(e)}")
            return False
    
    @staticmethod
    def ensure_directory_exists(dir_path: str) -> bool:
        """
        确保目录存在
        :param dir_path: 目录路径
        :return: 是否成功
        """
        try:
            os.makedirs(dir_path, exist_ok=True)
            log.info(f"确保目录存在: {dir_path}")
            return True
        except Exception as e:
            log.error(f"创建目录失败: {dir_path} - {str(e)}")
            return False

# 创建全局文件操作实例
file_operations = FileOperations()