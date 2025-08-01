# -*- coding: utf-8 -*-
"""按钮样式管理模块"""

from PySide6.QtWidgets import QPushButton
from PySide6.QtCore import Qt

class ButtonStyle:
    """按钮样式管理类"""

    @staticmethod
    def apply_primary_style(button: QPushButton) -> None:
        """应用主要按钮样式

        Args:
            button: 要应用样式的按钮
        """
        button.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)

    @staticmethod
    def apply_success_style(button: QPushButton) -> None:
        """应用成功按钮样式

        Args:
            button: 要应用样式的按钮
        """
        button.setStyleSheet("""
            QPushButton {
                background-color: #107c10;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0e6b0d;
            }
            QPushButton:pressed {
                background-color: #0a530a;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)

    @staticmethod
    def apply_warning_style(button: QPushButton) -> None:
        """应用警告按钮样式

        Args:
            button: 要应用样式的按钮
        """
        button.setStyleSheet("""
            QPushButton {
                background-color: #ff8c00;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e67e00;
            }
            QPushButton:pressed {
                background-color: #cc7a00;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)

    @staticmethod
    def apply_danger_style(button: QPushButton) -> None:
        """应用危险按钮样式

        Args:
            button: 要应用样式的按钮
        """
        button.setStyleSheet("""
            QPushButton {
                background-color: #e81123;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d13438;
            }
            QPushButton:pressed {
                background-color: #a4262c;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)

    @staticmethod
    def apply_secondary_style(button: QPushButton) -> None:
        """应用次要按钮样式

        Args:
            button: 要应用样式的按钮
        """
        button.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                color: #333333;
                border: 1px solid #cccccc;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
            QPushButton:disabled {
                background-color: #f5f5f5;
                color: #a0a0a0;
                border: 1px solid #e0e0e0;
            }
        """)
