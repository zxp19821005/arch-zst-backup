#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import signal
import json
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

from modules.logger import log
from modules.config_manager import config_manager

class ArchZstBackupApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 1. 确保日志系统初始化前设置级别
        config_path = os.path.join(
            os.path.expanduser('~/.config/arch-zst-backup'),
            'config.json'
        )
        log_level = 'INFO'  # 默认值
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    log_level = config.get('log_level', 'INFO')
            except Exception as e:
                print(f"读取配置文件失败: {e}")
        try:
            if os.path.exists(config_path):
                with open(config_path) as f:
                    log_config = json.load(f)
                    log_level = log_config.get('level', 'INFO')
        except Exception:
            pass
        
        # 强制设置日志级别，确保在第一条日志前生效
        log.set_level(log_level)
        
        # 2. 加载主配置
        self.config = config_manager.load_config()
        
        # 3. 初始化应用程序
        log.info(f"初始化应用程序，当前日志级别: {log_level}")
        
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
            ("日志显示", LogPage()),
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
        
        # 默认选择首页
        self.menu_list.setCurrentRow(0)
        
        log.info("主窗口UI设置完成")

    def switch_page(self, index):
        """切换页面"""
        try:
            self.stacked_widget.setCurrentIndex(index)
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
            sys.exit()

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