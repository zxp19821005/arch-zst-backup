#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import signal
import json
from pathlib import Path

# 动态添加项目根目录到模块搜索路径
# 确保项目本地的 modules 目录优先级高于全局安装的模块
sys.path.insert(0, str(Path(__file__).parent.parent))
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QSystemTrayIcon, QMenu,
    QListWidget, QStackedWidget, QVBoxLayout, QHBoxLayout, QWidget,
    QListWidgetItem, QTabWidget
)
from PySide6.QtGui import QIcon, QAction, QFont
from PySide6.QtCore import Qt, QSize, QTimer

from pages.settings_page import SettingsPage
from pages.log_page import LogPage
from pages.backup_manager_page import BackupManagerPage
from pages.cache_manager_page import CacheManagerPage
from ui.components.status_bar import StatusBar

from modules.logger import log
from modules.config_manager import config_manager
log.set_level('DEBUG')  # 设置为DEBUG级别

class ArchZstBackupApp(QMainWindow):
    """Arch Linux软件包备份工具主窗口"""

    def __init__(self):
        super().__init__()

        # 1. 设置日志文件和日志级别
        # 设置日志文件路径到配置目录下的logs子目录
        config_dir = os.path.expanduser("~/.config/arch-zst-backup")
        logs_dir = os.path.join(config_dir, "logs")
        os.makedirs(logs_dir, exist_ok=True)
        log_file_path = os.path.join(logs_dir, "app.log")
        log.set_log_file(log_file_path)
        
        # 从主配置文件读取日志级别，默认为INFO
        log_level = 'INFO'
        try:
            config = config_manager.load_config()
            log_level = config.get('logLevel', 'INFO')
        except Exception:
            pass

        # 强制设置日志级别，确保在第一条日志前生效
        log.set_level(log_level)

        # 2. 加载主配置
        self.config = config_manager.load_config()

        # 3. 初始化应用程序
        log.info(f"初始化应用程序，当前日志级别: {log_level}")
        
        # 4. 执行日志管理
        retention_days = self.config.get('logRetentionDays', 30)
        log.manage_logs(retention_days)

        # 设置窗口标题和图标
        self.setWindowTitle("Arch Linux 软件包备份工具")
        self.setWindowIcon(QIcon("src/assets/icon.png"))

        # 初始化托盘图标
        self.init_tray_icon()

        # 设置主窗口大小
        self.resize(800, 600)

        # 初始化标签页控件
        self.tab_widget = QTabWidget()

        # 优化标签页与内容的间距
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #ddd;
                padding: 10px;
                margin-top: -1px;
            }
        """)

        # 初始化UI
        self.setup_ui()

        # 设置标签页样式
        self.setStyleSheet("""
            QTabBar::tab {
                background: #f0f0f0;
                border: 1px solid #ccc;
                padding: 8px 12px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                transition: background 0.3s ease;
            }
            QTabBar::tab:selected {
                background: #fff;
                border-bottom-color: #fff;
            }
            QTabBar::tab:hover {
                background: #e0e0e0;
            }
        """)

        log.info("应用程序初始化完成")

    def setup_ui(self):
        """设置主窗口UI"""
        central_widget = QWidget()
        central_widget.setContentsMargins(0, 0, 0, 0)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 横向菜单栏
        self.menu_list = QListWidget()
        self.menu_list.setFixedHeight(50)
        self.menu_list.setFlow(QListWidget.LeftToRight)
        self.menu_list.setFont(QFont("Arial", 10))

        self.menu_list.setStyleSheet("""
            QListWidget {
                background-color: #2d2d2d;
                color: #ffffff;
                border: none;
                font-size: 14px;
            }
            QListWidget::item {
                padding: 10px 20px;
                border-right: 1px solid #3d3d3d;
            }
            QListWidget::item:selected {
                background-color: #3d3d3d;
                color: #ffffff;
            }
        """)

        # 添加菜单项
        menu_items = [
            ("备份软件管理", BackupManagerPage()),
            ("缓存软件管理", CacheManagerPage()),
            ("日志", LogPage()),
            ("设置", SettingsPage())
        ]

        for text, page in menu_items:
            item = QListWidgetItem(text)
            item.setTextAlignment(Qt.AlignCenter)
            self.menu_list.addItem(item)

        # 页面堆栈
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setContentsMargins(0, 0, 0, 0)

        # 添加页面到堆栈
        for _, page in menu_items:
            if page:
                self.stacked_widget.addWidget(page)
            else:
                placeholder = QWidget()
                self.stacked_widget.addWidget(placeholder)

        # 连接菜单选择信号
        self.menu_list.currentRowChanged.connect(self.switch_page)

        # 设置布局
        menu_layout = QHBoxLayout()
        menu_layout.addWidget(self.menu_list)
        main_layout.addLayout(menu_layout)
        main_layout.addWidget(self.stacked_widget)
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # 初始化状态栏
        self.status_bar = StatusBar(self)
        self.setStatusBar(self.status_bar)

        # 默认选择首页，但不触发信号
        self.menu_list.blockSignals(True)
        self.menu_list.setCurrentRow(0)
        self.menu_list.blockSignals(False)
        
        # 不在启动时自动刷新页面，等待用户手动操作
        
        log.info("主窗口UI设置完成")

    def switch_page(self, index):
        """切换页面"""
        try:
            # 获取当前页面索引
            current_index = self.stacked_widget.currentIndex()
            
            # 设置新的页面索引
            self.stacked_widget.setCurrentIndex(index)
            
            # 处理页面切换逻辑
            if index == 0:  # 备份管理页面
                # 不自动刷新，等待用户手动操作
                self.status_bar.show_permanent_message(
                    "备份软件管理页面，请点击刷新按钮加载软件包列表"
                )
            elif index == 1:  # 缓存软件管理页面
                # 不自动刷新，等待用户手动操作
                self.status_bar.show_permanent_message(
                    "缓存软件管理页面，请点击刷新按钮加载软件包列表"
                )
        except Exception as e:
            log.error(f"切换页面失败: {str(e)}")

    def init_tray_icon(self):
        log.info("初始化托盘图标...")
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon("src/assets/tray.png"))

        # 创建托盘菜单
        tray_menu = QMenu()

        # 添加菜单项
        show_action = QAction("显示主窗口", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)

        quit_action = QAction("退出", self)
        quit_action.triggered.connect(sys.exit)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        log.info("托盘图标初始化完成")

    def closeEvent(self, event):
        close_behavior = self.config.get('closeBehavior', 'exit')

        if close_behavior == 'minimize':
            log.info("收到关闭事件，最小化到托盘")
            event.ignore()
            self.hide()
        else:
            log.info("收到关闭事件，退出程序")
            super().closeEvent(event)
            QApplication.instance().quit()

def handle_sigint(signum, frame):
    """处理Ctrl+C信号"""
    QApplication.instance().quit()

def main():
    app = QApplication(sys.argv)

    # 注册信号处理
    signal.signal(signal.SIGINT, handle_sigint)

    # 确保应用程序使用正确的图标主题
    # 高DPI支持设置已移除，因PyQt6 API变更

    window = ArchZstBackupApp()
    window.show()

    # 创建定时器检查信号
    timer = QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)  # 让事件循环处理信号

    sys.exit(app.exec())

if __name__ == "__main__":
    main()