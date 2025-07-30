# -*- coding: utf-8 -*-
"""主窗口模块"""

from .main_window import MainWindowWrapper
from .ui_init import UIInitMixin
from .table_operations import TableOperationsMixin
from .ui_buttons import UIButtonsMixin
from .system_tray import SystemTrayMixin

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
