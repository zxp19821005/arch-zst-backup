#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
缓存服务模块

提供系统缓存相关的业务逻辑，如检查更新、清理缓存等
"""

from PySide6.QtWidgets import QMessageBox
from PySide6.QtCore import QProcess
from modules.logger import log
from utils.decorators import handle_operation_errors

class CacheService:
    """缓存服务类，处理所有与系统缓存相关的业务逻辑"""

    def __init__(self, cache_manager):
        """初始化缓存服务

        Args:
            cache_manager: 缓存管理器实例
        """
        self.cache_manager = cache_manager

    @handle_operation_errors
    def check_for_updates(self):
        """检查系统更新"""
        log.info("开始检查系统更新")
        try:
            self.cache_manager.process = QProcess()
            self.cache_manager.process.finished.connect(lambda: self.cache_manager.on_update_finished())
            self.cache_manager.process.errorOccurred.connect(self.cache_manager.on_update_error)

            # 调用终端执行命令
            command = "xterm"
            args = ["-e", "bash", "-c", "paru; read -p '按回车键退出...'"]
            log.debug(f"执行命令: {command} {args}")
            self.cache_manager.process.start(command, args)

            if not self.cache_manager.process.waitForStarted(5000):
                log.error("启动更新检查进程失败")
                QMessageBox.critical(self.cache_manager, "错误", "无法启动更新检查进程")
        except Exception as e:
            log.error(f"检查更新时发生错误: {str(e)}")
            QMessageBox.critical(self.cache_manager, "错误", f"检查更新失败: {str(e)}")

    @handle_operation_errors
    def clean_cache(self):
        """清理系统缓存"""
        log.info("开始清理系统缓存")
        try:
            self.cache_manager.process = QProcess()
            self.cache_manager.process.finished.connect(lambda: self.cache_manager.on_clean_finished())
            self.cache_manager.process.errorOccurred.connect(self.cache_manager.on_clean_error)

            # 调用终端执行命令
            command = "xterm"
            args = ["-e", "bash", "-c", "paru -Scc; read -p '按回车键退出...'"]
            log.debug(f"执行命令: {command} {args}")
            self.cache_manager.process.start(command, args)

            if not self.cache_manager.process.waitForStarted(5000):
                log.error("启动缓存清理进程失败")
                QMessageBox.critical(self.cache_manager, "错误", "无法启动缓存清理进程")
        except Exception as e:
            log.error(f"清理缓存时发生错误: {str(e)}")
            QMessageBox.critical(self.cache_manager, "错误", f"清理缓存失败: {str(e)}")

    @handle_operation_errors
    def clean_system_cache(self):
        """清理系统缓存（使用pkexec）"""
        confirm = QMessageBox.question(
            self.cache_manager, "确认清理",
            "确定要清理系统缓存吗？此操作将删除所有未安装软件包的缓存文件",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if confirm != QMessageBox.StandardButton.Yes:
            return

        process = QProcess()
        # 使用bash管道自动输入4次y确认
        process.setProgram("bash")
        process.setArguments(["-c", "printf 'y\n\ny\n\n' | pkexec paru -Scc"])

        def handle_output():
            output = process.readAllStandardOutput().data().decode()
            log.info(f"清理输出: {output}")

        def handle_error():
            error = process.readAllStandardError().data().decode()
            # 过滤掉交互提示文本
            if not error.strip().startswith("::"):
                log.error(f"清理错误: {error}")

        def handle_finished(exit_code, exit_status):
            if exit_code == 0:
                QMessageBox.information(self.cache_manager, "完成", "系统缓存清理成功")
                log.success("系统缓存清理成功")
            else:
                QMessageBox.warning(self.cache_manager, "警告", f"缓存清理失败 (退出码: {exit_code})")
                log.warning(f"缓存清理失败 (退出码: {exit_code})")

        process.readyReadStandardOutput.connect(handle_output)
        process.readyReadStandardError.connect(handle_error)
        process.finished.connect(handle_finished)

        process.start()
