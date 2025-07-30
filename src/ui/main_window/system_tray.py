# -*- coding: utf-8 -*-
"""系统托盘混入类"""

from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import Qt

class SystemTrayMixin:
    """系统托盘相关的方法混入类"""
    
    def init_system_tray(self):
        """初始化系统托盘"""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            self.logger.warning("系统不支持系统托盘")
            return
        
        # 创建托盘图标
        self.tray_icon = QSystemTrayIcon(self)
        
        # 设置图标
        icon = self.get_tray_icon()
        self.tray_icon.setIcon(icon)
        
        # 创建托盘菜单
        self.create_tray_menu()
        
        # 连接信号
        self.tray_icon.activated.connect(self.on_tray_activated)
        
        # 显示托盘
        config = self.config_manager.get_config()
        show_tray = config.get('ui', {}).get('show_tray', True)
        if show_tray:
            self.tray_icon.show()
        
        self.logger.info("系统托盘初始化完成")
    
    def get_tray_icon(self):
        """获取托盘图标"""
        # 尝试加载自定义图标
        try:
            icon = QIcon(":/icons/tray.png")
            if not icon.isNull():
                return icon
        except:
            pass
        
        # 使用默认图标
        return self.style().standardIcon(self.style().StandardPixmap.SP_ComputerIcon)
    
    def create_tray_menu(self):
        """创建托盘菜单"""
        tray_menu = QMenu()
        
        # 显示/隐藏主窗口
        show_action = QAction("显示主窗口", self)
        show_action.triggered.connect(self.show_main_window)
        tray_menu.addAction(show_action)
        
        hide_action = QAction("隐藏主窗口", self)
        hide_action.triggered.connect(self.hide_main_window)
        tray_menu.addAction(hide_action)
        
        tray_menu.addSeparator()
        
        # 快速操作
        backup_action = QAction("快速备份", self)
        backup_action.triggered.connect(self.quick_backup)
        tray_menu.addAction(backup_action)
        
        restore_action = QAction("快速还原", self)
        restore_action.triggered.connect(self.quick_restore)
        tray_menu.addAction(restore_action)
        
        tray_menu.addSeparator()
        
        # 设置和退出
        settings_action = QAction("设置", self)
        settings_action.triggered.connect(self.show_settings)
        tray_menu.addAction(settings_action)
        
        quit_action = QAction("退出", self)
        quit_action.triggered.connect(self.quit_application)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
    
    def on_tray_activated(self, reason):
        """托盘图标激活处理"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.toggle_main_window()
        elif reason == QSystemTrayIcon.ActivationReason.Trigger:
            # 单击显示通知或切换窗口
            pass
    
    def show_main_window(self):
        """显示主窗口"""
        self.show()
        self.raise_()
        self.activateWindow()
    
    def hide_main_window(self):
        """隐藏主窗口"""
        self.hide()
    
    def toggle_main_window(self):
        """切换主窗口显示状态"""
        if self.isVisible():
            self.hide_main_window()
        else:
            self.show_main_window()
    
    def quick_backup(self):
        """快速备份"""
        self.logger.info("执行快速备份")
        self.show_tray_message("快速备份", "备份操作已开始...")
        # 具体备份逻辑由子类实现
    
    def quick_restore(self):
        """快速还原"""
        self.logger.info("执行快速还原")
        self.show_tray_message("快速还原", "还原操作已开始...")
        # 具体还原逻辑由子类实现
    
    def show_settings(self):
        """显示设置页面"""
        self.show_main_window()
        if hasattr(self, 'tabs'):
            # 切换到设置标签页
            for i in range(self.tabs.count()):
                if self.tabs.tabText(i) == "设置":
                    self.tabs.setCurrentIndex(i)
                    break
    
    def quit_application(self):
        """退出应用"""
        self.logger.info("用户从托盘退出应用")
        self.close()
    
    def show_tray_message(self, title, message, icon=QSystemTrayIcon.MessageIcon.Information, timeout=3000):
        """显示托盘消息"""
        if hasattr(self, 'tray_icon') and self.tray_icon.isVisible():
            self.tray_icon.showMessage(title, message, icon, timeout)
    
    def closeEvent(self, event):
        """重写关闭事件"""
        config = self.config_manager.get_config()
        close_action = config.get('ui', {}).get('close_action', 'minimize')
        
        if close_action == 'minimize' and hasattr(self, 'tray_icon') and self.tray_icon.isVisible():
            # 最小化到托盘
            event.ignore()
            self.hide()
            self.show_tray_message(
                "Arch Zst Backup", 
                "应用程序已最小化到系统托盘",
                QSystemTrayIcon.MessageIcon.Information,
                2000
            )
        else:
            # 直接退出
            event.accept()
            super().closeEvent(event)
