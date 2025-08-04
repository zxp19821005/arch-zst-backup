#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
终端执行器模块

提供在终端中执行命令的功能
"""

from PySide6.QtCore import QProcess
from modules.logger import log
from src.utils.terminal_utils import get_terminal_args
from modules.config_manager import config_manager

class TerminalExecutor:
    """
    终端执行器类，负责在终端中执行命令
    
    此类提供了一个统一的接口，用于在各种终端模拟器中执行命令。
    它支持多种终端模拟器，并能够处理命令执行完成后的回调函数。
    
    Attributes:
        process (QProcess): 用于执行命令的进程对象
    
    Examples:
        >>> executor = TerminalExecutor()
        >>> executor.execute_command("ls -la")
        True
        >>> executor.execute_paru_command()
        True
    """

    def __init__(self):
        """
        初始化终端执行器
        
        创建一个新的 QProcess 对象，用于后续执行命令。
        """
        self.process = QProcess()

    def execute_command(self, command_str, finished_callback=None, error_callback=None):
        """
        在终端中执行命令
        
        此方法在用户配置的终端模拟器中执行指定的命令。它会自动添加
        "read -p '按Enter键关闭窗口...'" 到命令末尾，以便用户能够查看
        命令的输出结果。

        Args:
            command_str (str): 要执行的命令字符串，例如 "ls -la" 或 "paru -Syu"
            finished_callback (function, optional): 命令执行完成后的回调函数，
                不接受任何参数
            error_callback (function, optional): 命令执行出错时的回调函数，
                接受一个 QProcess.ProcessError 参数

        Returns:
            bool: 是否成功启动命令。如果成功启动返回 True，否则返回 False
            
        Examples:
            >>> def on_finished():
            ...     print("命令执行完成")
            >>> def on_error(error):
            ...     print(f"命令执行出错: {error}")
            >>> executor = TerminalExecutor()
            >>> executor.execute_command("ls -la", on_finished, on_error)
            True
        """
        try:
            # 检查命令字符串是否为空
            if not command_str or not command_str.strip():
                log.error("命令字符串为空")
                return False
                
            # 加载配置
            try:
                config = config_manager.load_config()
                terminal = config.get('terminal', 'xterm')
                log.debug(f"使用终端模拟器: {terminal}")
            except Exception as e:
                log.error(f"加载配置失败: {str(e)}")
                terminal = 'xterm'  # 使用默认终端
                log.debug(f"使用默认终端模拟器: {terminal}")

            # 获取终端参数
            try:
                terminal_arg = get_terminal_args(terminal)
                log.debug(f"终端参数: {terminal_arg}")
            except Exception as e:
                log.error(f"获取终端参数失败: {str(e)}")
                terminal_arg = ["-e"]  # 使用默认参数
                log.debug(f"使用默认终端参数: {terminal_arg}")

            # 构建完整命令
            # 使用更可靠的方式来保持终端窗口打开
            full_command = f"{command_str} && echo '命令执行完成，按Enter键关闭窗口...' && read"
            args = terminal_arg + ["bash", "-c", full_command]
            log.debug(f"完整命令: {terminal} {args}")

            # 检查进程状态
            if self.process.state() != QProcess.NotRunning:
                log.warning("终端进程已经在运行，尝试终止现有进程")
                try:
                    self.process.terminate()
                    if not self.process.waitForFinished(3000):
                        log.warning("无法正常终止进程，尝试强制终止")
                        self.process.kill()
                except Exception as e:
                    log.error(f"终止现有进程时出错: {str(e)}")
                    # 创建新的进程对象
                    self.process = QProcess()

            # 连接信号
            try:
                if finished_callback:
                    self.process.finished.connect(finished_callback)
                    log.debug("已连接完成回调函数")
                if error_callback:
                    self.process.errorOccurred.connect(error_callback)
                    log.debug("已连接错误回调函数")
            except Exception as e:
                log.error(f"连接回调函数时出错: {str(e)}")

            # 执行命令
            try:
                log.info(f"在终端中执行命令: {command_str}")
                self.process.start(terminal, args)
            except Exception as e:
                log.error(f"启动终端进程时出错: {str(e)}")
                return False

            # 等待进程启动
            if not self.process.waitForStarted(5000):
                error_msg = "无法启动终端进程"
                if self.process.error() != QProcess.UnknownError:
                    error_msg += f": {self.process.errorString()}"
                log.error(error_msg)
                return False

            log.debug("终端进程已成功启动")
            return True

        except Exception as e:
            log.error(f"执行终端命令时发生未预期的错误: {str(e)}", exc_info=True)
            return False

    def execute_paru_command(self, finished_callback=None, error_callback=None):
        """
        执行 paru 命令
        
        此方法是一个便捷方法，用于在终端中执行 paru 命令。
        paru 是一个 Arch Linux 的 AUR 助手，用于管理软件包。
        
        Args:
            finished_callback (function, optional): 命令执行完成后的回调函数，
                不接受任何参数
            error_callback (function, optional): 命令执行出错时的回调函数，
                接受一个 QProcess.ProcessError 参数

        Returns:
            bool: 是否成功启动命令。如果成功启动返回 True，否则返回 False
            
        Examples:
            >>> def on_finished():
            ...     print("paru 命令执行完成")
            >>> def on_error(error):
            ...     print(f"paru 命令执行出错: {error}")
            >>> executor = TerminalExecutor()
            >>> executor.execute_paru_command(on_finished, on_error)
            True
        """
        return self.execute_command("paru", finished_callback, error_callback)

    def execute_clean_command(self, finished_callback=None, error_callback=None):
        """
        执行清理命令
        
        此方法是一个便捷方法，用于在终端中执行 paru -Scc 命令。
        这个命令会清理 pacman 和 paru 的缓存，包括未使用的软件包和旧版本。
        
        Args:
            finished_callback (function, optional): 命令执行完成后的回调函数，
                不接受任何参数
            error_callback (function, optional): 命令执行出错时的回调函数，
                接受一个 QProcess.ProcessError 参数

        Returns:
            bool: 是否成功启动命令。如果成功启动返回 True，否则返回 False
            
        Examples:
            >>> def on_finished():
            ...     print("清理命令执行完成")
            >>> def on_error(error):
            ...     print(f"清理命令执行出错: {error}")
            >>> executor = TerminalExecutor()
            >>> executor.execute_clean_command(on_finished, on_error)
            True
        """
        return self.execute_command("paru -Scc", finished_callback, error_callback)
        
    def get_process_state(self):
        """
        获取当前进程状态
        
        Returns:
            str: 进程状态的描述字符串
        """
        state = self.process.state()
        if state == QProcess.NotRunning:
            return "NotRunning"
        elif state == QProcess.Starting:
            return "Starting"
        elif state == QProcess.Running:
            return "Running"
        else:
            return f"Unknown ({state})"
            
    def get_process_error(self):
        """
        获取当前进程错误
        
        Returns:
            tuple: (错误代码, 错误描述)
        """
        error = self.process.error()
        error_string = self.process.errorString()
        
        error_descriptions = {
            QProcess.FailedToStart: "进程启动失败",
            QProcess.Crashed: "进程崩溃",
            QProcess.Timedout: "进程超时",
            QProcess.WriteError: "写入错误",
            QProcess.ReadError: "读取错误",
            QProcess.UnknownError: "未知错误"
        }
        
        description = error_descriptions.get(error, f"未知错误代码 ({error})")
        if error_string:
            description += f": {error_string}"
            
        return error, description
        
    def terminate_process(self, force=False):
        """
        终止当前进程
        
        Args:
            force (bool): 是否强制终止进程。如果为 True，则使用 kill() 方法；
                        如果为 False，则使用 terminate() 方法
                        
        Returns:
            bool: 是否成功终止进程
        """
        if self.process.state() == QProcess.NotRunning:
            log.debug("进程未运行，无需终止")
            return True
            
        try:
            if force:
                log.debug("强制终止进程")
                self.process.kill()
            else:
                log.debug("正常终止进程")
                self.process.terminate()
                
            # 等待进程结束
            if self.process.waitForFinished(3000):
                log.debug("进程已成功终止")
                return True
            else:
                log.warning("进程未在指定时间内终止")
                return False
                
        except Exception as e:
            log.error(f"终止进程时出错: {str(e)}")
            return False
