#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextEdit
from PySide6.QtCore import Qt
from modules.logger import log

class LogPage(QWidget):
    """日志显示页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        log.info("初始化日志显示页面")
        self.setup_ui()

    def setup_ui(self):
        """设置页面UI"""
        main_layout = QVBoxLayout()

        # 日志显示区域
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        main_layout.addWidget(self.log_display)

        self.setLayout(main_layout)
        log.info("日志显示页面UI设置完成")

    def update_log(self, log_content):
        """更新日志内容"""
        self.log_display.setPlainText(log_content)