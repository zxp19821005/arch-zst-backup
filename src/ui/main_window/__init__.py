# -*- coding: utf-8 -*-
"""主窗口模块"""

from src.ui.main_window.main_window import MainWindowWrapper
from src.ui.main_window.ui_init import UIInitMixin
from src.ui.main_window.table_operations import TableOperationsMixin
from src.ui.main_window.ui_buttons import UIButtonsMixin
from src.ui.main_window.system_tray import SystemTrayMixin

# 使用MainWindowWrapper作为MainWindow
MainWindow = MainWindowWrapper

__all__ = [
    'MainWindow',
    'MainWindowWrapper',
    'UIInitMixin',
    'TableOperationsMixin',
    'UIButtonsMixin',
    'SystemTrayMixin'
]
