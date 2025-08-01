#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
优化后的缓存管理器页面

该文件整合了UI、业务逻辑和服务层，实现了模块化的缓存管理功能。
"""

from pathlib import Path
from PySide6.QtWidgets import QWidget
from modules.logger import log
from .cache_manager_ui import CacheManagerUI
from src.business.backup_service import BackupService
from src.business.package_service import PackageService
from src.business.cache_service import CacheService
from src.business.cache_manager_operations import CacheManagerOperations

class CacheManagerPage(QWidget):
    """缓存软件管理页面"""

    # 常量定义
    PACMAN_CACHE_PATH = '/var/cache/pacman/pkg'
    PARU_CACHE_PATH = Path.home() / '.cache/paru/clone'
    YAY_CACHE_PATH = Path.home() / '.cache/yay'

    def __init__(self, parent=None):
        super().__init__(parent)
        log.info("初始化缓存软件管理页面")
        self.packages = []
        self.list_display_manager = None
        self.process = None

        # 初始化UI
        self.ui = CacheManagerUI(self)

        # 初始化服务层
        self.backup_service = BackupService(self)
        self.package_service = PackageService(self)
        self.cache_service = CacheService(self)

        # 连接信号和槽
        self.connect_signals()

    def connect_signals(self):
        """连接UI信号到服务方法"""
        self.ui.scan_button.clicked.connect(self.package_service.scan_cache_dirs)
        self.ui.dedupe_button.clicked.connect(self.package_service.deduplicate_packages)
        self.ui.delete_button.clicked.connect(self.package_service.delete_selected)
        self.ui.update_button.clicked.connect(self.cache_service.check_for_updates)
        self.ui.clean_cache_button.clicked.connect(self.cache_service.clean_cache)
        self.ui.backup_newer_button.clicked.connect(self.backup_service.backup_newer_versions)
        self.ui.backup_to_subdir_button.clicked.connect(self.backup_service.backup_to_subdirectory)

    def on_update_finished(self):
        """更新完成处理"""
        self.process = None

        # 执行刷新操作，确保列表更新
        log.info("更新检查完成，执行刷新操作")
        if hasattr(self, 'scan_button'):
            # 模拟点击扫描按钮
            self.scan_button.click()
        elif hasattr(self, 'scan_cache_dirs'):
            # 直接调用扫描方法
            self.scan_cache_dirs()

    def on_clean_finished(self):
        """清理完成处理"""
        self.process = None

        # 执行刷新操作，确保列表更新
        log.info("缓存清理完成，执行刷新操作")
        if hasattr(self, 'scan_button'):
            # 模拟点击扫描按钮
            self.scan_button.click()
        elif hasattr(self, 'scan_cache_dirs'):
            # 直接调用扫描方法
            self.scan_cache_dirs()

    def on_update_error(self, error):
        """更新检查错误处理"""
        log.error(f"更新检查进程错误: {self.process.errorString()}")
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.critical(self, "错误", f"更新检查进程错误: {self.process.errorString()}")

    def on_clean_error(self, error):
        """缓存清理错误处理"""
        log.error(f"缓存清理进程错误: {self.process.errorString()}")
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.critical(self, "错误", f"缓存清理进程错误: {self.process.errorString()}")

    def reset_data(self):
        """重置数据状态"""
        self.packages = []
        self.list_display_manager = None
        self.ui.setup_ui()

    def handle_filter(self, keyword):
        """处理过滤信号"""
        log.info(f"过滤关键词: {keyword}")
        # 调用表格管理器的过滤方法，300ms延迟
        self.list_display_manager.filter_data(search_text=keyword)
        log.info("缓存软件管理页面UI设置完成")

    def load_existing_packages(self):
        """加载现有的软件包列表"""
        from modules.config_manager import config_manager
        from pathlib import Path
        import json
        from PySide6.QtWidgets import QMessageBox
        from ui.components.button_style import ButtonStyle

        config_dir = Path(config_manager.config_dir)
        log.debug(f"配置目录路径: {config_dir}")
        packages_file = config_dir / "updated_packages.json"
        log.debug(f"尝试读取文件: {packages_file}")

        if packages_file.exists():
            try:
                with open(packages_file, 'r', encoding='utf-8') as f:
                    self.packages = json.load(f)
                    log.debug(f"读取到 {len(self.packages)} 条软件包数据")
                    if not isinstance(self.packages, list):
                        log.error(f"无效的数据格式: {type(self.packages)}")
                        raise ValueError("Invalid packages data format")

                    if not self.packages:
                        log.warning(f"软件包列表为空: {packages_file}")
                        self.packages = []  # 确保是空列表
                    else:
                        log.info(f"从 {packages_file} 加载了 {len(self.packages)} 个软件包")
                    self.update_table()
            except Exception as e:
                log.error(f"加载软件包列表失败: {str(e)}", exc_info=True)
                log.debug(f"完整异常堆栈:", stack_info=True)
                self.packages = []  # 确保是空列表
                self.update_table()  # 使用空列表更新表格
                msg_box = QMessageBox(QMessageBox.Critical, "错误", f"加载软件包列表失败: {str(e)}")
                ok_btn = msg_box.addButton("确定", QMessageBox.AcceptRole)
                ButtonStyle.apply_danger_style(ok_btn)
                msg_box.exec()

    def update_table(self):
        """更新表格显示"""
        if self.list_display_manager is None:
            self._init_list_display()

        if self.list_display_manager is not None:
            self.list_display_manager.update_table(self.packages)
        else:
            raise RuntimeError("列表显示管理器初始化失败")

    def _init_list_display(self):
        """初始化列表显示管理器"""
        if self.ui.table_widget is None:
            raise RuntimeError("表格组件未初始化")

        # 使用预定义的列配置
        from ui.components.list_display_manager import COLUMN_CONFIGS, ListDisplayManager
        column_config = COLUMN_CONFIGS["cache_manager"]

        self.list_display_manager = ListDisplayManager(self.ui.table_widget, column_config)

    def get_selected_packages(self):
        """获取选中的软件包"""
        return self.list_display_manager.get_selected_packages(self.packages)

    def update_status_bar(self):
        """更新状态栏信息"""
        duplicate_count = self.count_duplicate_packages()
        backupable_count = self.count_backupable_packages()
        if self.parent() and hasattr(self.parent(), 'parent') and self.parent().parent():
            main_window = self.parent().parent()
            if hasattr(main_window, 'status_bar') and len(self.packages) > 0:
                main_window.status_bar.show_permanent_message(
                    f"共 {len(self.packages)} 个软件包，其中有 {duplicate_count} 个重复软件包，有 {backupable_count} 个软件包可以备份"
                )

    def on_item_copied(self, content):
        """处理复制事件"""
        log.info(f"已复制内容到剪贴板: {content}")

    def on_item_renamed(self, old_path, new_path):
        """处理重命名事件"""
        log.info(f"文件已重命名: {old_path} -> {new_path}")
        # 不自动刷新，等待用户手动操作
        log.info("文件已重命名，请手动刷新以更新列表")

    def on_item_deleted(self, path):
        """处理删除事件"""
        log.info(f"文件已删除: {path}")
        
        # 执行刷新操作，确保列表更新
        log.info("文件已删除，执行刷新操作")
        if hasattr(self, 'scan_button'):
            # 模拟点击扫描按钮
            self.scan_button.click()
        elif hasattr(self, 'scan_cache_dirs'):
            # 直接调用扫描方法
            self.scan_cache_dirs()
            
    def handle_context_menu_delete(self, path):
        """处理右键菜单删除操作"""
        log.info(f"通过右键菜单删除文件: {path}")
        
        # 确认删除
        from PySide6.QtWidgets import QMessageBox
        from ui.components.button_style import ButtonStyle
        
        # 获取所有选中的文件路径
        selected = self.get_selected_packages()
        
        # 构建确认对话框文本
        if len(selected) == 1:
            confirm_text = f"确定要删除以下文件吗？\n\n{path}"
        else:
            confirm_text = f"以下是你需要删除的 {len(selected)} 个软件：\n\n"
            for i, pkg in enumerate(selected, 1):
                # 构建完整路径
                location = pkg.get("location", "")
                filename = pkg.get("filename", "")
                full_path = f"{location}/{filename}" if location else filename
                confirm_text += f"{i}. {full_path}\n"
            confirm_text += "\n确认删除吗？"
            
        msg_box = QMessageBox(QMessageBox.Question, "确认删除", confirm_text)
        yes_btn = msg_box.addButton("确认", QMessageBox.YesRole)
        no_btn = msg_box.addButton("取消", QMessageBox.NoRole)
        ButtonStyle.apply_primary_style(yes_btn)
        ButtonStyle.apply_secondary_style(no_btn)
        msg_box.setDefaultButton(no_btn)
        reply = msg_box.exec()
        
        if reply == QMessageBox.Yes:
            # 调用缓存管理器操作的删除方法
            # 使用所有选中的软件包
            if selected:
                # 使用缓存管理器操作的删除方法
                self.package_service.delete_selected_packages(selected)

    def count_duplicate_packages(self):
        """计算重复软件包数量"""
        from utils.common_utils import count_duplicate_packages
        return count_duplicate_packages(self.packages)

    def count_backupable_packages(self):
        """计算可备份软件包数量"""
        from utils.common_utils import count_backupable_packages
        return count_backupable_packages(self.packages)
        
    def scan_cache_dirs(self):
        """扫描缓存目录，委托给package_service处理"""
        return self.package_service.scan_cache_dirs()
