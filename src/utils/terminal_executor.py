#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
终端执行器模块

提供在终端中执行命令的功能
"""

from PySide6.QtCore import QProcess
from modules.logger import log
from .terminal_utils import get_terminal_args
from modules.config_manager import config_manager

class TerminalExecutor:
    """终端执行器类，负责在终端中执行命令"""

    def __init__(self):
        """初始化终端执行器"""
        self.process = QProcess()

    def execute_command(self, command_str, finished_callback=None, error_callback=None):
        """
        在终端中执行命令

        Args:
            command_str (str): 要执行的命令字符串
            finished_callback (function, optional): 命令执行完成后的回调函数
            error_callback (function, optional): 命令执行出错时的回调函数

        Returns:
            bool: 是否成功启动命令
        """
        try:
            # 加载配置
            config = config_manager.load_config()
            terminal = config.get('terminal', 'xterm')

            # 获取终端参数
            terminal_arg = get_terminal_args(terminal)

            # 构建完整命令
            args = terminal_arg + ["bash", "-c", f"{command_str}; read -p '按Enter键关闭窗口...'"]

            # 连接信号
            if finished_callback:
                self.process.finished.connect(finished_callback)
            if error_callback:
                self.process.errorOccurred.connect(error_callback)

            # 执行命令
            log.debug(f"执行命令: {terminal} {args}")
            self.process.start(terminal, args)

            # 等待进程启动
            if not self.process.waitForStarted(5000):
                log.error("无法启动终端进程")
                return False

            return True

        except Exception as e:
            log.error(f"执行终端命令时出错: {str(e)}")
            return False

    def execute_paru_command(self, finished_callback=None, error_callback=None):
        """
        执行 paru 命令

        Args:
            finished_callback (function, optional): 命令执行完成后的回调函数
            error_callback (function, optional): 命令执行出错时的回调函数

        Returns:
            bool: 是否成功启动命令
        """
        return self.execute_command("paru", finished_callback, error_callback)

    def execute_clean_command(self, finished_callback=None, error_callback=None):
        """
        执行清理命令

        Args:
            finished_callback (function, optional): 命令执行完成后的回调函数
            error_callback (function, optional): 命令执行出错时的回调函数

        Returns:
            bool: 是否成功启动命令
        """
        return self.execute_command("paru -Scc", finished_callback, error_callback)
