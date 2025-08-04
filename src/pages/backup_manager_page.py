#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
优化后的备份管理器页面

该文件整合了UI、业务逻辑和服务层，实现了模块化的备份管理功能。
"""

from pathlib import Path
from PySide6.QtWidgets import QWidget
from modules.logger import log
from src.pages.backup_manager_ui import BackupManagerUI
from src.business.backup_manager_operations import BackupManagerOperations
from ui.components.list_display_manager import ListDisplayManager


class BackupManagerPage(QWidget):
    """备份软件管理页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        log.info("初始化备份软件管理页面")
        self.packages = []
        self.list_display_manager = None
        self.process = None

        # 初始化UI
        self.ui = BackupManagerUI(self)

        # 初始化操作类
        self.operations = BackupManagerOperations(self)

        # 连接信号和槽
        self.connect_signals()

    def connect_signals(self):
        """连接UI信号到操作方法"""
        self.ui.scan_button.clicked.connect(self.operations.scan_backup_dir)
        self.ui.dedupe_button.clicked.connect(self.operations.deduplicate_packages)
        self.ui.delete_button.clicked.connect(self.operations.delete_selected)
        self.ui.install_button.clicked.connect(self.operations.install_selected)
        self.ui.filter_box.filter_signal.connect(self.handle_filter)
        # QTableWidget没有这些信号，所以不需要连接

    def handle_filter(self, keyword):
        """处理过滤信号"""
        log.info(f"过滤关键词: {keyword}")
        # 检查列表显示管理器是否已初始化
        if self.list_display_manager is None:
            try:
                self._init_list_display()
            except Exception as e:
                log.error(f"初始化列表显示管理器失败: {e}")
                return

        # 调用表格管理器的过滤方法
        self.list_display_manager.filter_data(search_text=keyword)
        log.info("备份软件管理页面UI设置完成")

    def load_existing_packages(self):
        """加载现有的软件包列表"""
        from modules.config_manager import config_manager
        import json
        from PySide6.QtWidgets import QMessageBox
        from ui.components.button_style import ButtonStyle

        config_dir = Path(config_manager.config_dir)
        packages_file = config_dir / "existing_packages.json"

        if packages_file.exists():
            try:
                with open(packages_file, 'r', encoding='utf-8') as f:
                    self.packages = json.load(f)
                    self.update_table()
                    log.info(f"从 {packages_file} 加载了 {len(self.packages)} 个软件包")
            except Exception as e:
                log.error(f"加载软件包列表失败: {str(e)}")
                msg_box = QMessageBox(QMessageBox.Critical, "错误", "加载软件包列表失败")
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
        from ui.components.list_display_manager import COLUMN_CONFIGS
        column_config = COLUMN_CONFIGS["backup_manager"]
        column_names = list(column_config.keys())
        self.list_display_manager = ListDisplayManager(self.ui.table_widget, column_config)

        # QTableWidget没有set_path_column方法，所以不需要设置

    def get_selected_packages(self):
        """获取选中的软件包"""
        return self.list_display_manager.get_selected_packages(self.packages)

    def update_status_bar(self):
        """更新状态栏信息"""
        duplicate_count = self.count_duplicate_packages()
        if self.parent() and hasattr(self.parent(), 'parent') and self.parent().parent():
            main_window = self.parent().parent()
            if hasattr(main_window, 'status_bar') and len(self.packages) > 0:
                main_window.status_bar.show_permanent_message(
                    f"共 {len(self.packages)} 个软件包，其中有 {duplicate_count} 个重复软件包"
                )

    def count_duplicate_packages(self):
        """计算重复软件包数量"""
        from utils.common_utils import count_duplicate_packages
        return count_duplicate_packages(self.packages)

    def on_install_finished(self):
        """安装完成处理"""
        self.process = None
        log.info("软件包安装完成")

    def on_install_error(self, error):
        """安装错误处理"""
        log.error(f"安装进程错误: {self.process.errorString()}")
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.critical(self, "错误", f"安装进程错误: {self.process.errorString()}")

