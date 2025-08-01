#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
UI处理功能模块
"""

import logging
from typing import List
from PySide6.QtWidgets import QMessageBox

from ui.components.button_style import ButtonStyle

log = logging.getLogger(__name__)


class UIHandler:
    """UI处理器，负责处理UI相关的功能"""

    def __init__(self, backup_manager):
        """初始化UI处理器

        Args:
            backup_manager: 备份管理器实例
        """
        self.backup_manager = backup_manager

    def show_warning(self, message: str) -> None:
        """显示警告对话框

        Args:
            message (str): 警告消息

        Returns:
            None
        """
        log.warning(f"显示警告对话框: {message}")
        msg_box = QMessageBox(QMessageBox.Warning, "警告", message)
        ok_btn = msg_box.addButton("确定", QMessageBox.AcceptRole)
        ButtonStyle.apply_primary_style(ok_btn)
        msg_box.exec()

    def show_error(self, message: str) -> None:
        """显示错误对话框

        Args:
            message (str): 错误消息

        Returns:
            None
        """
        log.error(f"显示错误对话框: {message}")
        QMessageBox.critical(self.backup_manager, "错误", message)

    def show_info(self, message: str) -> None:
        """显示信息对话框

        Args:
            message (str): 信息消息

        Returns:
            None
        """
        msg_box = QMessageBox(QMessageBox.Information, "信息", message)
        ok_btn = msg_box.addButton("确定", QMessageBox.AcceptRole)
        ButtonStyle.apply_primary_style(ok_btn)
        msg_box.exec()

    def show_confirmation(self, message: str, packages: List = None) -> bool:
        """显示确认对话框，返回用户选择结果

        Args:
            message (str): 确认消息
            packages (List, optional): 要删除的软件包列表，用于显示完整路径

        Returns:
            bool: 用户是否确认
        """
        # 如果提供了软件包列表，构建更详细的确认对话框
        if packages and len(packages) > 0:
            # 使用集合来避免重复路径
            unique_paths = set()
            for pkg in packages:
                # 构建完整路径
                location = pkg.get("location", "")
                filename = pkg.get("filename", "")
                full_path = f"{location}/{filename}" if location else filename
                unique_paths.add(full_path)

            confirm_text = f"以下是你需要删除的 {len(unique_paths)} 个软件：\n\n"
            for i, path in enumerate(sorted(unique_paths), 1):
                confirm_text += f"{i}. {path}\n"
            confirm_text += "\n确认删除吗？"
        else:
            confirm_text = message

        msg_box = QMessageBox(QMessageBox.Question, "确认删除", confirm_text)
        yes_btn = msg_box.addButton("确认", QMessageBox.YesRole)
        no_btn = msg_box.addButton("取消", QMessageBox.NoRole)
        ButtonStyle.apply_primary_style(yes_btn)
        ButtonStyle.apply_secondary_style(no_btn)
        msg_box.setDefaultButton(no_btn)  # 设置"取消"为默认按钮
        result = msg_box.exec()
        clicked_button = msg_box.clickedButton()
        is_yes = clicked_button == yes_btn
        log.info(f"确认对话框返回值: {result}, 点击的是'确认'按钮: {is_yes}")
        return is_yes

    def update_status_bar_with_message(self, message: str, fallback_message: str) -> None:
        """更新状态栏消息

        Args:
            message (str): 主要消息
            fallback_message (str): 备用消息，当没有软件包时使用
        """
        main_window = self.backup_manager.window()
        if hasattr(main_window, 'status_bar'):
            if self.backup_manager.packages:
                main_window.status_bar.show_permanent_message(message)
            else:
                main_window.status_bar.show_permanent_message(fallback_message)
