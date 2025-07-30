#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QTextEdit, QHBoxLayout, 
                            QCheckBox, QComboBox, QPushButton, QSpacerItem, QSizePolicy, QLabel)
from PySide6.QtCore import Qt, QTimer
from modules.logger import log
import os
from datetime import datetime

class LogPage(QWidget):
    """日志显示页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        log.info("初始化日志显示页面")
        
        # 初始化变量
        self.auto_scroll = True
        self.current_log_level = "ALL"
        
        self.setup_ui()
        
        # 不再使用自动刷新定时器
        
        # 初始加载日志
        self.refresh_log()

    def setup_ui(self):
        """设置页面UI"""
        main_layout = QVBoxLayout()

        # 日志显示区域
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        # 启用自动换行，移除横向滚动条
        self.log_display.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.log_display.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        # 启用HTML格式支持，用于彩色日志
        self.log_display.setHtml('<div style="font-family: monospace; white-space: pre-wrap;">等待加载日志...</div>')
        main_layout.addWidget(self.log_display)
        
        # 控制区域
        control_layout = QHBoxLayout()
        
        # 自动滚动复选框
        self.auto_scroll_checkbox = QCheckBox("自动滚动")
        self.auto_scroll_checkbox.setChecked(self.auto_scroll)
        self.auto_scroll_checkbox.stateChanged.connect(self.toggle_auto_scroll)
        control_layout.addWidget(self.auto_scroll_checkbox)
        
        # 日志级别下拉框
        control_layout.addWidget(QLabel("日志级别:"))
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["ALL", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR"])
        self.log_level_combo.setCurrentText(self.current_log_level)
        self.log_level_combo.currentTextChanged.connect(self.change_log_level)
        control_layout.addWidget(self.log_level_combo)
        
        # 添加弹性空间
        control_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        
        # 刷新日志按钮
        self.refresh_button = QPushButton("刷新日志")
        self.refresh_button.clicked.connect(self.refresh_log)
        control_layout.addWidget(self.refresh_button)
        
        # 清除日志按钮
        self.clear_button = QPushButton("清除日志")
        self.clear_button.clicked.connect(self.clear_log)
        control_layout.addWidget(self.clear_button)
        
        main_layout.addLayout(control_layout)

        self.setLayout(main_layout)
        log.info("日志显示页面UI设置完成")

    def refresh_log(self):
        """刷新日志内容"""
        try:
            # 尝试从正确的日志文件位置读取
            log_path = os.path.join(os.path.expanduser("~/.config"), "arch-zst-backup", "logs", "app.log")
            
            log_content = "暂无日志内容\n"
            
            if os.path.exists(log_path):
                try:
                    with open(log_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                        # 添加调试信息
                        log.info(f"日志文件存在，共读取到 {len(lines)} 行日志")
                        if len(lines) > 0:
                            log.info(f"第一行日志: {lines[0].strip()}")
                            log.info(f"最后一行日志: {lines[-1].strip()}")
                        # 只显示最后100行日志
                        if len(lines) > 100:
                            lines = lines[-100:]
                        
                        # 根据选择的日志级别过滤日志
                        if self.current_log_level != "ALL":
                            filtered_lines = []
                            for line in lines:
                                if f"[{self.current_log_level}]" in line:
                                    filtered_lines.append(line)
                            lines = filtered_lines
                        else:
                            # 如果选择ALL级别，但仍然不显示INFO级别的日志，可能是其他问题
                            # 让我们添加一些调试信息
                            log.info(f"读取到 {len(lines)} 行日志")
                        
                        # 转换为彩色HTML日志
                        log_content = self.convert_to_colorful_html(lines)
                except Exception as e:
                    log.error(f"读取日志文件 {log_path} 失败: {e}")
            
            # 添加时间戳
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # 添加时间戳
            header = f'<div style="color: #555; font-weight: bold;">=== 日志更新时间: {timestamp} ===</div>'
            
            # 使用HTML格式更新日志
            html_content = f'<div style="font-family: monospace; white-space: pre-wrap;">{header}<br/>{log_content}</div>'
            
            self.update_log_html(html_content)
        except Exception as e:
            log.error(f"刷新日志失败: {e}")
            self.update_log(f"加载日志失败: {e}")
    
    def update_log(self, log_content):
        """更新日志内容"""
        self.log_display.setPlainText(log_content)
        # 如果启用了自动滚动，滚动到底部
        if self.auto_scroll:
            scrollbar = self.log_display.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
    
    def toggle_auto_scroll(self, state):
        """切换自动滚动状态"""
        self.auto_scroll = (state == Qt.CheckState.Checked.value)
    
    def change_log_level(self, level):
        """更改日志级别过滤"""
        self.current_log_level = level
        # 立即刷新日志以应用新的过滤级别
        self.refresh_log()
    
    def clear_log(self):
        """清除日志显示"""
        self.log_display.clear()
    
    def convert_to_colorful_html(self, lines):
        """将日志行转换为彩色HTML格式"""
        html_lines = []
        
        # 日志级别颜色映射
        color_map = {
            "DEBUG": "#6C7A89",    # 灰色
            "INFO": "#3498DB",      # 蓝色
            "SUCCESS": "#2ECC71",   # 绿色
            "WARNING": "#F39C12",   # 橙色
            "ERROR": "#E74C3C"      # 红色
        }
        
        for line in lines:
            line = line.strip()
            if not line:
                html_lines.append("<br/>")
                continue
                
            # 检查是否包含日志级别标记
            for level, color in color_map.items():
                if f"[{level}]" in line:
                    # 使用正则表达式匹配日志级别和时间戳部分
                    import re
                    pattern = rf"(\[{level}\]) (\d{{4}}-\d{{2}}-\d{{2}} \d{{2}}:\d{{2}}:\d{{2}}) - (.*)"
                    match = re.match(pattern, line)
                    if match:
                        level_tag, timestamp, message = match.groups()
                        html_line = f'<span style="color:{color}">{level_tag} {timestamp} - {message}</span>'
                        html_lines.append(html_line)
                        break
            else:
                # 如果没有匹配到日志级别，直接添加原文本
                html_lines.append(line)
        
        return "<br/>".join(html_lines)
    
    def update_log_html(self, html_content):
        """使用HTML格式更新日志内容"""
        self.log_display.setHtml(html_content)
        # 如果启用了自动滚动，滚动到底部
        if self.auto_scroll:
            scrollbar = self.log_display.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())