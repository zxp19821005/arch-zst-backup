# -*- coding: utf-8 -*-
"""状态栏组件"""

from PySide6.QtWidgets import QStatusBar, QLabel, QProgressBar
from PySide6.QtCore import Qt, QTimer

class StatusBar(QStatusBar):
    """增强的状态栏组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
        # 自动清除消息的定时器
        self.clear_timer = QTimer()
        self.clear_timer.timeout.connect(self.clear_temporary_message)
        self.clear_timer.setSingleShot(True)
    
    def setup_ui(self):
        """设置UI"""
        # 主状态标签
        self.status_label = QLabel("")
        self.addWidget(self.status_label)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumWidth(200)
        self.addPermanentWidget(self.progress_bar)
        
        # 计数标签
        self.count_label = QLabel("")
        self.addPermanentWidget(self.count_label)
        
        # 时间标签
        self.time_label = QLabel("")
        self.addPermanentWidget(self.time_label)
    
    def show_message(self, message, timeout=0):
        """显示消息"""
        self.status_label.setText(message)
        if timeout > 0:
            self.clear_timer.start(timeout * 1000)
    
    def show_permanent_message(self, message):
        """显示永久消息"""
        self.status_label.setText(message)
        self.clear_timer.stop()
    
    def clear_temporary_message(self):
        """清除临时消息"""
        # 不再自动设置为"就绪"，保留最后一条消息
        pass
    
    def show_progress(self, value, maximum=100):
        """显示进度"""
        self.progress_bar.setMaximum(maximum)
        self.progress_bar.setValue(value)
        self.progress_bar.setVisible(True)
    
    def hide_progress(self):
        """隐藏进度条"""
        self.progress_bar.setVisible(False)
    
    def update_count(self, total=0, selected=0, filtered=0):
        """更新计数显示"""
        if selected > 0:
            text = f"总计: {total}, 已选: {selected}"
            if filtered != total:
                text += f", 过滤后: {filtered}"
        elif filtered != total:
            text = f"总计: {total}, 显示: {filtered}"
        else:
            text = f"总计: {total}"
        
        self.count_label.setText(text)
    
    def update_time(self, time_text):
        """更新时间显示"""
        self.time_label.setText(time_text)
