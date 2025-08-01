#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from functools import wraps
from PySide6.QtWidgets import QMessageBox
from modules.logger import log

def handle_errors(func):
    """错误处理装饰器

    用于统一处理方法中的异常，记录日志并显示错误消息
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except Exception as e:
            method_name = func.__name__
            log.error(f"{method_name} 失败: {str(e)}")
            QMessageBox.critical(self if hasattr(self, 'window') else None, "错误", f"{method_name} 失败: {str(e)}")
    return wrapper

def handle_operation_errors(func):
    """操作错误处理装饰器

    专门用于处理操作类方法中的异常，记录日志并显示错误消息
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except Exception as e:
            method_name = func.__name__
            log.error(f"{method_name} 失败: {str(e)}")
            QMessageBox.critical(self.cache_manager, "错误", f"{method_name} 失败: {str(e)}")
    return wrapper
