# -*- coding: utf-8 -*-
"""
主窗口模块，整合其他所有模块
"""
import os
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QTabWidget
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon

# 导入混入类
from .ui_init import UIInitMixin
from .table_operations import TableOperationsMixin
from .ui_buttons import UIButtonsMixin
from .system_tray import SystemTrayMixin

# 导入页面
from src.pages.backup_manager_page import BackupManagerPage
from src.pages.cache_manager_page import CacheManagerPage
from src.pages.settings_page import SettingsPage
from src.pages.log_page import LogPage

# 导入模块
import sys
from pathlib import Path
# 动态添加项目根目录到模块搜索路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from modules.logger import log
from modules.config_manager import config_manager

class MainWindowWrapper(QMainWindow, UIInitMixin, TableOperationsMixin, 
                       UIButtonsMixin, SystemTrayMixin):
    """主窗口包装器，整合所有功能"""
    
    def __init__(self):
        super().__init__()
        
        # 初始化配置和日志
        self.config_manager = config_manager
        self.logger = log
        
        # 初始化UI
        self.init_ui()
        
        # 初始化系统托盘
        self.init_system_tray()
        
        # 连接信号
        self.connect_signals()
        
        self.logger.info("主窗口初始化完成")
    
    def init_ui(self):
        """初始化用户界面"""
        # 设置窗口属性
        self.setWindowTitle("Arch Zst Backup Manager")
        self.setMinimumSize(1000, 700)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 创建标签页控件
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # 初始化各个页面
        self.init_pages()
        
        # 设置状态栏
        self.setup_status_bar()
        
        # 应用主题
        self.apply_theme()
        
        self.logger.info("UI初始化完成")
    
    def init_pages(self):
        """初始化各个页面"""
        # 备份管理页面
        self.backup_manager_page = BackupManagerPage()
        self.tabs.addTab(self.backup_manager_page, "备份管理")
        
        # 缓存管理页面
        self.cache_manager_page = CacheManagerPage()
        self.tabs.addTab(self.cache_manager_page, "缓存管理")
        
        # 设置页面
        self.settings_page = SettingsPage()
        self.tabs.addTab(self.settings_page, "设置")
        
        # 日志页面
        self.log_page = LogPage()
        self.tabs.addTab(self.log_page, "日志")
    
    def connect_signals(self):
        """连接信号槽"""
        # 连接设置页面的信号
        if hasattr(self.settings_page, 'settings_changed'):
            self.settings_page.settings_changed.connect(self.apply_settings)
    
    def apply_settings(self):
        """应用设置更改"""
        self.logger.info("应用设置更改")
        # 刷新各页面显示
        if hasattr(self.backup_manager_page, 'refresh_display'):
            self.backup_manager_page.refresh_display()
        if hasattr(self.cache_manager_page, 'refresh_display'):
            self.cache_manager_page.refresh_display()
        
        # 重新应用主题
        self.apply_theme()
