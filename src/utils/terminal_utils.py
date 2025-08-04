#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
终端工具模块

提供与终端模拟器相关的工具函数
"""

def get_terminal_args(terminal_name):
    """
    获取终端模拟器的命令行参数

    Args:
        terminal_name (str): 终端模拟器名称

    Returns:
        list: 终端模拟器的命令行参数列表
    """
    # 终端模拟器参数映射表
    terminal_args_map = {
        "xterm": ["-e"],
        "gnome-terminal": ["--"],
        "konsole": ["-e"],
        "terminator": ["-x"],
        "xfce4-terminal": ["-x"],
        "lxterminal": ["-e"]
    }

    # 获取当前终端的参数，如果没有找到则使用默认的 -e
    return terminal_args_map.get(terminal_name, ["-e"])
