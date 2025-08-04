# -*- coding: utf-8 -*-
"""
主窗口模块，整合其他所有模块
"""
import os
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QTabWidget
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon

# 导入混入类
from src.ui.main_window.ui_init import UIInitMixin
from src.ui.main_window.table_operations import TableOperationsMixin
from src.ui.main_window.ui_buttons import UIButtonsMixin
from src.ui.main_window.system_tray import SystemTrayMixin

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
        
        # 标记标签页是否首次访问
        self.backup_tab_visited = False
        self.cache_tab_visited = False
        
        # 初始化UI
        self.init_ui()
        
        # 初始化系统托盘
        self.init_system_tray()
        
        # 连接信号
        self.connect_signals()
        
        # 程序启动后直接触发备份管理页面的刷新操作
        self.logger.info("程序启动完成，直接触发备份管理页面刷新")
        if hasattr(self.backup_manager_page, 'scan_backup_dir'):
            self.backup_manager_page.scan_backup_dir()
            
            # 获取软件包列表并分析重复软件
            packages = self.backup_manager_page.packages
            total_count = len(packages)
            
            # 分析重复软件
            from modules.version_comparator import version_comparator
            duplicate_count = 0
            grouped = {}
            for pkg in packages:
                key = (pkg['name'], pkg['arch'])
                grouped.setdefault(key, []).append(pkg)
            
            for (name, arch), pkgs in grouped.items():
                if len(pkgs) > 1:
                    duplicate_count += len(pkgs) - 1  # 减去保留的最新版本
            
            # 在状态栏显示结果
            if hasattr(self, 'status_bar') and hasattr(self.status_bar, 'show_message'):
                result_msg = f"当前共有{total_count}个软件包，其中有{duplicate_count}个重复软件包"
                self.status_bar.show_message(result_msg, 5000)
                
                # 更新状态栏计数显示
                if hasattr(self.status_bar, 'update_count'):
                    self.status_bar.update_count(total=total_count, selected=0, filtered=total_count)
                    
            # 标记备份管理页面已访问
            self.backup_tab_visited = True
            
            # 获取软件包列表并分析重复软件
            packages = self.backup_manager_page.packages
            total_count = len(packages)
            
            # 分析重复软件
            from modules.version_comparator import version_comparator
            duplicate_count = 0
            grouped = {}
            for pkg in packages:
                key = (pkg['name'], pkg['arch'])
                grouped.setdefault(key, []).append(pkg)
            
            for (name, arch), pkgs in grouped.items():
                if len(pkgs) > 1:
                    duplicate_count += len(pkgs) - 1  # 减去保留的最新版本
            
            # 在状态栏显示结果
            if hasattr(self, 'status_bar') and hasattr(self.status_bar, 'show_message'):
                result_msg = f"当前共有{total_count}个软件包，其中有{duplicate_count}个重复软件包"
                self.status_bar.show_message(result_msg, 5000)
                
                # 更新状态栏计数显示
                if hasattr(self.status_bar, 'update_count'):
                    self.status_bar.update_count(total=total_count, selected=0, filtered=total_count)

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
            
        # 连接标签页切换信号
        self.tabs.currentChanged.connect(self.on_tab_changed)
    
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
        
    def on_tab_changed(self, index):
        """标签页切换事件处理"""
        tab_name = self.tabs.tabText(index)
        self.logger.info(f"切换到标签页: {tab_name}")
        
        # 使用自定义状态栏显示刷新消息
        if hasattr(self, 'status_bar') and hasattr(self.status_bar, 'show_message'):
            self.status_bar.show_message(f"正在刷新{tab_name}页面...", 0)
        
        # 根据标签页名称执行相应刷新操作
        if tab_name == "备份管理":
            if hasattr(self.backup_manager_page, 'scan_backup_dir') and not self.backup_tab_visited:
                try:
                        self.logger.info("首次访问备份管理页面，开始扫描备份目录...")
                        self.backup_manager_page.scan_backup_dir()
                        self.backup_tab_visited = True
                        self.logger.info("备份目录扫描完成")
                        
                        # 获取软件包列表并分析重复软件
                        packages = self.backup_manager_page.packages
                        total_count = len(packages)
                        
                        # 分析重复软件
                        from modules.version_comparator import version_comparator
                        duplicate_count = 0
                        grouped = {}
                        for pkg in packages:
                            key = (pkg['name'], pkg['arch'])
                            grouped.setdefault(key, []).append(pkg)
                        
                        for (name, arch), pkgs in grouped.items():
                            if len(pkgs) > 1:
                                duplicate_count += len(pkgs) - 1  # 减去保留的最新版本
                        
                        # 在状态栏显示结果
                        if hasattr(self, 'status_bar') and hasattr(self.status_bar, 'show_message'):
                            result_msg = f"当前共有{total_count}个软件包，其中有{duplicate_count}个重复软件包"
                            self.status_bar.show_message(result_msg, 5000)
                            
                            # 更新状态栏计数显示
                            if hasattr(self.status_bar, 'update_count'):
                                self.status_bar.update_count(total=total_count, selected=0, filtered=total_count)
                    else:
                        # 非首次访问，只显示简要信息
                        if hasattr(self, 'status_bar') and hasattr(self.status_bar, 'show_message'):
                            packages = self.backup_manager_page.packages
                            total_count = len(packages)
                            self.status_bar.show_message(f"备份软件管理页面，共 {total_count} 个软件", 3000)
                            
                            # 更新状态栏计数显示
                            if hasattr(self.status_bar, 'update_count'):
                                self.status_bar.update_count(total=total_count, selected=0, filtered=total_count)
                except Exception as e:
                    self.logger.error(f"刷新备份管理页面失败: {str(e)}")
                    if hasattr(self, 'status_bar') and hasattr(self.status_bar, 'show_message'):
                        self.status_bar.show_message(f"刷新{tab_name}页面失败: {str(e)}", 5000)
                        
        elif tab_name == "缓存管理":
            if hasattr(self.cache_manager_page, 'scan_cache_dirs') and not self.cache_tab_visited:
                try:
                        self.logger.info("首次访问缓存管理页面，开始扫描缓存目录...")
                        self.cache_manager_page.scan_cache_dirs()
                        self.cache_tab_visited = True
                        self.logger.info("缓存目录扫描完成")
                        
                        # 获取软件包列表并分析
                        packages = self.cache_manager_page.packages
                        total_count = len(packages)
                        
                        # 分析重复软件和可备份软件
                        from modules.version_comparator import version_comparator
                        duplicate_count = 0
                        backupable_count = 0
                        
                        # 按名称分组软件包
                        packages_by_name = {}
                        for pkg in packages:
                            name = pkg['name']
                            if name not in packages_by_name:
                                packages_by_name[name] = []
                            packages_by_name[name].append(pkg)
                        
                        # 分析重复软件和可备份软件
                        for name, pkgs in packages_by_name.items():
                            if len(pkgs) > 1:
                                duplicate_count += len(pkgs) - 1  # 减去保留的最新版本
                        
                        # 简化处理，假设所有软件都可以备份
                        backupable_count = len(packages)
                        
                        # 在状态栏显示结果
                        if hasattr(self, 'status_bar') and hasattr(self.status_bar, 'show_message'):
                            result_msg = f"当前共有{total_count}个软件包，其中有{duplicate_count}个重复软件包，有{backupable_count}个软件包可以进行备份"
                            self.status_bar.show_message(result_msg, 5000)
                            
                            # 更新状态栏计数显示
                            if hasattr(self.status_bar, 'update_count'):
                                self.status_bar.update_count(total=total_count, selected=0, filtered=total_count)
                    else:
                        # 非首次访问，只显示简要信息
                        if hasattr(self, 'status_bar') and hasattr(self.status_bar, 'show_message'):
                            packages = self.cache_manager_page.packages
                            total_count = len(packages)
                            self.status_bar.show_message(f"缓存软件管理页面，共 {total_count} 个软件", 3000)
                            
                            # 更新状态栏计数显示
                            if hasattr(self.status_bar, 'update_count'):
                                self.status_bar.update_count(total=total_count, selected=0, filtered=total_count)
                except Exception as e:
                    self.logger.error(f"刷新缓存管理页面失败: {str(e)}")
                    if hasattr(self, 'status_bar') and hasattr(self.status_bar, 'show_message'):
                        self.status_bar.show_message(f"刷新{tab_name}页面失败: {str(e)}", 5000)
