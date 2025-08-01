#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional, Tuple
from .logger import log
from PySide6.QtWidgets import QInputDialog, QLineEdit, QMessageBox

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
            # 替换路径中的非法字符
            dest = os.path.normpath(dest.replace(':', '-'))
            try:
                shutil.copy2(src, dest)
                return True
            except Exception as e:
                log.error(f"拷贝文件失败: {str(e)}")
                return False
            log.success(f"文件拷贝成功: {src} -> {dest}")
            return True
            
        except PermissionError:
            log.error(f"没有权限拷贝文件: {src}")
            return False
        except Exception as e:
            log.info(f"拷贝文件时出错: {str(e)}")
            return False
    
    @staticmethod
    def delete_file(file_path: str) -> bool:
        """
        安全删除文件，如果普通权限删除失败，会提示是否使用root权限删除
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
                # 询问用户是否使用root权限删除
                from PySide6.QtWidgets import QApplication
                if QApplication.instance():
                    msg_box = QMessageBox(
                        QMessageBox.Question,
                        "需要管理员权限", 
                        f"文件 {os.path.basename(file_path)} 需要管理员权限才能删除。\n\n是否使用管理员权限删除？"
                    )
                    yes_btn = msg_box.addButton("是", QMessageBox.YesRole)
                    no_btn = msg_box.addButton("否", QMessageBox.NoRole)
                    # 移除 ButtonStyle 依赖
                    msg_box.setDefaultButton(no_btn)
                    reply = msg_box.exec()
                    
                    if reply == QMessageBox.Yes:
                        return FileOperations.delete_file_with_root(file_path)
                    else:
                        return False
                else:
                    log.info("尝试使用root权限删除文件")
                    return FileOperations.delete_file_with_root(file_path)
            
            # 执行删除
            log.info(f"正在删除文件: {file_path}")
            os.remove(file_path)
            log.success(f"文件删除成功: {file_path}")
            return True
            
        except PermissionError:
            log.error(f"没有权限删除文件: {file_path}")
            # 询问用户是否使用root权限删除
            from PySide6.QtWidgets import QApplication
            if QApplication.instance():
                msg_box = QMessageBox(
                    QMessageBox.Question,
                    "需要管理员权限", 
                    f"文件 {os.path.basename(file_path)} 需要管理员权限才能删除。\n\n是否使用管理员权限删除？"
                )
                yes_btn = msg_box.addButton("是", QMessageBox.YesRole)
                no_btn = msg_box.addButton("否", QMessageBox.NoRole)
                # 移除 ButtonStyle 依赖
                msg_box.setDefaultButton(no_btn)
                reply = msg_box.exec()
                
                if reply == QMessageBox.Yes:
                    return FileOperations.delete_file_with_root(file_path)
                else:
                    return False
            else:
                log.info("尝试使用root权限删除文件")
                return FileOperations.delete_file_with_root(file_path)
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

    @staticmethod
    def rename_file(old_path: str, new_path: str) -> bool:
        """
        安全重命名文件
        :param old_path: 原文件路径
        :param new_path: 新文件路径
        :return: 是否成功
        """
        try:
            # 检查源文件是否存在
            if not os.path.isfile(old_path):
                log.error(f"源文件不存在: {old_path}")
                return False
            
            # 检查源文件是否可写
            if not os.access(old_path, os.W_OK):
                log.error(f"源文件不可写: {old_path}")
                return False
            
            # 检查目标路径是否已存在
            if os.path.exists(new_path):
                log.error(f"目标路径已存在: {new_path}")
                return False
            
            # 检查目标目录是否存在并可写
            dest_dir = os.path.dirname(new_path)
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
            
            # 执行重命名
            log.info(f"正在重命名文件: {old_path} -> {new_path}")
            os.rename(old_path, new_path)
            log.success(f"文件重命名成功: {old_path} -> {new_path}")
            return True
            
        except PermissionError:
            log.error(f"没有权限重命名文件: {old_path}")
            return False
        except Exception as e:
            log.error(f"重命名文件时出错: {str(e)}")
            return False

    @staticmethod
    def delete_file_with_root(file_path: str) -> bool:
        """
        使用root权限删除文件
        :param file_path: 要删除的文件路径
        :return: 是否成功
        """
        try:
            # 使用pkexec执行rm命令删除文件
            log.info(f"尝试使用root权限删除文件: {file_path}")
            result = subprocess.run(
                ["pkexec", "rm", "-f", file_path],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                log.success(f"使用root权限删除文件成功: {file_path}")
                return True
            else:
                log.error(f"使用root权限删除文件失败: {file_path}")
                log.error(f"错误信息: {result.stderr}")
                return False
                
        except Exception as e:
            log.error(f"使用root权限删除文件时出错: {str(e)}")
            return False

# 创建全局文件操作实例
file_operations = FileOperations()