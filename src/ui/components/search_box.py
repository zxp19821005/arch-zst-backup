#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from PySide6.QtWidgets import (QWidget, QHBoxLayout, QLineEdit)
from PySide6.QtCore import Signal, Qt, QTimer
from PySide6.QtGui import QPalette, QColor

class FilterBox(QWidget):
    """过滤框组件，支持实时过滤 name、ver 和 location"""
    filter_signal = Signal(str)  # 参数: 过滤关键词

    def __init__(self, parent=None):
        super().__init__(parent)
        # 设置延迟定时器，延迟500毫秒触发过滤
        self.delay_timer = QTimer()
        self.delay_timer.setSingleShot(True)
        self.delay_timer.timeout.connect(self.emit_filter_signal)
        self.delay_ms = 500  # 延迟时间（毫秒）
        
        # 设置组件背景为透明，以便更好地融入深色界面
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.setup_ui()

    def setup_ui(self):
        """设置UI布局"""
        layout = QHBoxLayout()

        # 过滤输入框
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("输入过滤关键词...")
        self.filter_input.textChanged.connect(self.on_text_changed)
        self.filter_input.setMaximumWidth(300)  # 设置最大宽度为300像素
        
        # 设置深色主题样式
        self.filter_input.setStyleSheet("""
            QLineEdit {
                background-color: #2D2D2D;
                color: #E0E0E0;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 4px 8px;
            }
            QLineEdit:focus {
                border: 1px solid #3A7BBA;
            }
            QLineEdit::placeholder {
                color: #909090;
            }
        """)
        
        layout.addWidget(self.filter_input)

        self.setLayout(layout)

    def on_text_changed(self):
        """文本变化时的处理函数，重置延迟定时器"""
        # 重启定时器，取消之前的触发请求
        self.delay_timer.stop()
        self.delay_timer.start(self.delay_ms)
        
    def emit_filter_signal(self):
        """触发过滤信号"""
        filter_keyword = self.filter_input.text()
        self.filter_signal.emit(filter_keyword)