#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QTextEdit, QPlainTextEdit, QHBoxLayout, 
                            QCheckBox, QComboBox, QPushButton, QSpacerItem, QSizePolicy, QLabel)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QTextCursor, QTextCharFormat, QColor, QFont
from modules.logger import log, LogLevelColors
import os
from datetime import datetime
from ui.components.button_style import ButtonStyle
class LogPage(QWidget):
    """日志显示页面"""
    def __init__(self, parent=None):
        super().__init__(parent)
        log.info("初始化日志显示页面")

        # 初始化变量
        self.auto_scroll = True
        self.current_log_level = "DEBUG"

        self.setup_ui()
        self.refresh_log()
    def setup_ui(self):
        """设置页面UI"""
        main_layout = QVBoxLayout()

        self.log_display = QPlainTextEdit()
        self.log_display.setReadOnly(True)

        self.log_display.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        self.log_display.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        font = QFont("Consolas, Monaco, monospace")
        self.log_display.setFont(font)

        self.log_display.setPlainText("等待加载日志...")
        main_layout.addWidget(self.log_display)

        control_layout = QHBoxLayout()

        self.auto_scroll_checkbox = QCheckBox("自动滚动")
        self.auto_scroll_checkbox.setChecked(self.auto_scroll)
        self.auto_scroll_checkbox.stateChanged.connect(self.toggle_auto_scroll)
        control_layout.addWidget(self.auto_scroll_checkbox)

        control_layout.addWidget(QLabel("日志级别:"))
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR"])
        self.log_level_combo.setCurrentText(self.current_log_level)
        self.log_level_combo.currentTextChanged.connect(self.change_log_level)
        control_layout.addWidget(self.log_level_combo)

        control_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        self.refresh_button = QPushButton("刷新日志")
        self.refresh_button.clicked.connect(self.refresh_log)
        ButtonStyle.apply_primary_style(self.refresh_button)
        control_layout.addWidget(self.refresh_button)

        self.clear_button = QPushButton("清除日志")
        self.clear_button.clicked.connect(self.clear_log)
        ButtonStyle.apply_warning_style(self.clear_button)
        control_layout.addWidget(self.clear_button)

        main_layout.addLayout(control_layout)
        self.setLayout(main_layout)
        log.info("日志显示页面UI设置完成")
    def refresh_log(self):
        """刷新日志内容"""
        try:
            log_path = os.path.join(os.path.expanduser("~/.config"), "arch-zst-backup", "logs", "app.log")
            log_content = "暂无日志内容\n"
            if os.path.exists(log_path):
                try:
                    with open(log_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                        log.info(f"日志文件存在，共读取到 {len(lines)} 行日志")
                        if len(lines) > 0:
                            log.info(f"第一行日志: {lines[0].strip()}")
                            log.info(f"最后一行日志: {lines[-1].strip()}")
                        if len(lines) > 100:
                            lines = lines[-100:]

                        # 根据日志级别过滤日志
                        if self.current_log_level == "DEBUG":
                            # DEBUG级别显示所有日志
                            pass
                        else:
                            # 其他级别只显示对应级别及更高级别的日志
                            level_priority = {"DEBUG": 0, "INFO": 1, "SUCCESS": 2, "WARNING": 3, "ERROR": 4}
                            current_level_priority = level_priority.get(self.current_log_level, 4)
                            
                            filtered_lines = []
                            for line in lines:
                                for level, priority in level_priority.items():
                                    if f"[{level}]" in line and priority >= current_level_priority:
                                        filtered_lines.append(line)
                                        break
                            lines = filtered_lines

                        log_content = "".join(lines)
                except Exception as e:
                    log.error(f"读取日志文件 {log_path} 失败: {e}")

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            header = f"=== 日志更新时间: {timestamp} ==="

            plain_content = f"{header}\n{log_content}"
            self.update_log(plain_content)
        except Exception as e:
            log.error(f"刷新日志失败: {e}")
            self.update_log(f"加载日志失败: {e}")
    def update_log(self, log_content):
        """更新日志内容"""

        self.log_display.clear()

        cursor = self.log_display.textCursor()
        cursor.movePosition(QTextCursor.Start)

        lines = log_content.split("\n")
        for i, line in enumerate(lines):
            self.format_log_line(cursor, line)

            if i < len(lines) - 1:
                cursor.insertText("\n")

        if self.auto_scroll:
            scrollbar = self.log_display.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
    def toggle_auto_scroll(self, state):
        """切换自动滚动状态"""
        self.auto_scroll = (state == Qt.CheckState.Checked.value)
    def change_log_level(self, level):
        """更改日志级别过滤"""
        self.current_log_level = level

        self.refresh_log()
    def clear_log(self):
        """清除日志显示"""
        self.log_display.clear()

    def format_log_line(self, cursor, line):
        """为日志行设置格式和颜色"""

        color_map = {
            "DEBUG": QColor(*[int(LogLevelColors.DEBUG.value[0].lstrip("#")[i:i+2], 16) for i in (0, 2, 4)]),
            "INFO": QColor(*[int(LogLevelColors.INFO.value[0].lstrip("#")[i:i+2], 16) for i in (0, 2, 4)]),
            "SUCCESS": QColor(*[int(LogLevelColors.SUCCESS.value[0].lstrip("#")[i:i+2], 16) for i in (0, 2, 4)]),
            "WARNING": QColor(*[int(LogLevelColors.WARNING.value[0].lstrip("#")[i:i+2], 16) for i in (0, 2, 4)]),
            "ERROR": QColor(*[int(LogLevelColors.ERROR.value[0].lstrip("#")[i:i+2], 16) for i in (0, 2, 4)])
        }

        for level, color in color_map.items():
            if f"[{level}]" in line:

                level_marker = f"[{level}]"
                parts = line.split(level_marker, 1)

                if parts[0]:
                    cursor.insertText(parts[0])

                format = QTextCharFormat()
                format.setForeground(color)
                format.setFontWeight(QFont.Bold)
                cursor.setCharFormat(format)

                cursor.insertText(level_marker)

                # 重置格式
                cursor.setCharFormat(QTextCharFormat())

                # 插入剩余部分（如果有）
                if len(parts) > 1 and parts[1]:
                    cursor.insertText(parts[1])

                return

        # 如果没有日志级别标记，直接插入整行
        cursor.insertText(line)
