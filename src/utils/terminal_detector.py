#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
终端模拟器检测工具
"""

import os
import subprocess
from typing import List

def detect_installed_terminals() -> List[str]:
    """检测系统中已安装的终端模拟器

    Returns:
        List[str]: 已安装的终端模拟器列表
    """
    # 常见的终端模拟器列表
    common_terminals = [
        "xterm", "gnome-terminal", "konsole", "xfce4-terminal", 
        "lxterminal", "mate-terminal", "deepin-terminal", 
        "alacritty", "kitty", "terminator", "rxvt", "urxvt",
        "st", "lxterminal", "qterminal", "tilix", "guake",
        "tilda", "yakuake", "cool-retro-term", "hyper"
    ]

    installed_terminals = []

    # 检查每个终端模拟器是否已安装
    for terminal in common_terminals:
        try:
            # 使用 which 命令检查终端模拟器是否在 PATH 中
            result = subprocess.run(['which', terminal], 
                                  stdout=subprocess.PIPE, 
                                  stderr=subprocess.PIPE, 
                                  text=True)
            if result.returncode == 0:
                installed_terminals.append(terminal)
        except Exception:
            # 如果检查失败，忽略该终端模拟器
            pass

    return installed_terminals
