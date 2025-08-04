#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
终端工具模块

提供与终端模拟器相关的工具函数
"""

def get_terminal_args(terminal_name):
    """
    获取终端模拟器的命令行参数

    此函数根据终端模拟器的名称返回相应的命令行参数，用于在终端中执行命令。
    不同的终端模拟器使用不同的参数来指定要执行的命令。
    参数映射表从配置文件中加载，如果配置文件中没有找到对应的终端，
    则使用默认参数 ["-e"]。

    Args:
        terminal_name (str): 终端模拟器名称，如 "xterm"、"gnome-terminal"、"konsole" 等

    Returns:
        list: 终端模拟器的命令行参数列表，例如 ["-e"] 或 ["--"]

    Examples:
        >>> get_terminal_args("xterm")
        ["-e"]
        >>> get_terminal_args("gnome-terminal")
        ["--"]
        >>> get_terminal_args("unknown_terminal")
        ["-e"]  # 默认参数
    """
    try:
        # 从配置管理器加载配置
        from modules.config_manager import config_manager
        config = config_manager.load_config()
        
        # 从配置中获取终端参数映射表
        terminal_args_map = config.get('terminalArgsMap', {})
        
        # 获取当前终端的参数，如果没有找到则使用默认的 -e
        return terminal_args_map.get(terminal_name, ["-e"])
    except Exception as e:
        # 如果加载配置失败，使用硬编码的默认映射表
        from modules.logger import log
        log.warning(f"加载终端参数映射表失败: {str(e)}，使用默认映射表")
        
        # 默认终端模拟器参数映射表
        default_terminal_args_map = {
            "xterm": ["-e"],
            "gnome-terminal": ["--"],
            "konsole": ["-e"],
            "terminator": ["-x"],
            "xfce4-terminal": ["-x"],
            "lxterminal": ["-e"]
        }
        
        # 获取当前终端的参数，如果没有找到则使用默认的 -e
        return default_terminal_args_map.get(terminal_name, ["-e"])
