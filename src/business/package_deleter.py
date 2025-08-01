#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
软件包删除功能模块
"""

import logging
from typing import List, Tuple, Dict
from pathlib import Path

log = logging.getLogger(__name__)


class PackageDeleter:
    """软件包删除器，负责处理软件包删除相关的业务逻辑"""

    def __init__(self, ui_handler):
        """初始化删除器

        Args:
            ui_handler: UI处理器实例，用于显示对话框和更新UI
        """
        self.ui_handler = ui_handler

    def confirm_and_delete_packages(self, to_delete: List[Dict]) -> Tuple[int, List[str]]:
        """确认并删除软件包

        Args:
            to_delete (List[Dict]): 需要删除的软件包列表

        Returns:
            Tuple[int, List[str]]: (成功删除的数量, 失败的文件列表)
        """
        # 确认删除
        confirm = self.ui_handler.show_confirmation(
            f"确定要删除 {len(to_delete)} 个旧版本软件包吗？\n"
            "将保留每个软件包的最新版本。"
        )
        if not confirm:
            log.info("用户取消了去重操作")
            return 0, []

        log.info(f"开始执行删除操作，共 {len(to_delete)} 个文件")

        # 执行删除
        success_count, failed_files = self.execute_deletion(to_delete)

        log.info(f"删除操作完成: 成功 {success_count} 个，失败 {len(failed_files)} 个")

        return success_count, failed_files

    def execute_deletion(self, packages: List[Dict]) -> Tuple[int, List[str]]:
        """执行删除操作，返回成功数量和失败文件列表

        该方法会遍历软件包列表，尝试删除每个软件包对应的文件。
        对于每个文件，会检查必要的字段是否存在，然后尝试删除。
        删除过程中会处理各种异常情况，如权限不足、文件不存在等。

        Args:
            packages (List[Dict]): 要删除的软件包列表，每个软件包应包含location和filename字段

        Returns:
            Tuple[int, List[str]]: (成功删除的数量, 失败的文件路径列表)
        """
        from modules.file_operations import file_operations

        success_count = 0
        failed_files = []

        for pkg in packages:
            # 检查必要的字段是否存在
            if 'location' not in pkg or 'filename' not in pkg:
                log.error(f"软件包数据缺少必要字段: {pkg}")
                failed_files.append(f"无效数据: {pkg.get('filename', '未知文件名')}")
                continue

            # 尝试获取文件路径，优先使用fullpath字段（如果存在）
            file_path = None
            if 'fullpath' in pkg and pkg['fullpath']:
                file_path = Path(pkg['fullpath'])
            else:
                file_path = Path(pkg['location']) / pkg['filename']

            try:
                log.info(f"尝试删除文件: {file_path}")
                if file_operations.delete_file(str(file_path)):
                    success_count += 1
                    log.info(f"已删除: {file_path}")
                else:
                    failed_files.append(str(file_path))
                    log.warning(f"删除失败: {file_path}")
            except PermissionError as e:
                log.error(f"删除文件失败，权限不足: {file_path}")
                log.error(f"错误详情: {str(e)}")
                failed_files.append(str(file_path))
            except FileNotFoundError:
                log.warning(f"删除文件失败，文件不存在: {file_path}")
                # 文件不存在视为删除成功
                success_count += 1
                log.info(f"文件已不存在，视为删除成功: {file_path}")
            except OSError as e:
                log.error(f"删除文件失败，系统错误: {file_path}")
                log.error(f"错误详情: {str(e)}")
                failed_files.append(str(file_path))
            except Exception as e:
                log.error(f"删除文件时发生未知错误: {file_path}")
                log.error(f"错误详情: {str(e)}")
                failed_files.append(str(file_path))

        return success_count, failed_files

    def generate_result_message(self, to_delete: List[Dict], success_count: int, failed_files: List[str]) -> str:
        """生成操作结果消息

        Args:
            to_delete (List[Dict]): 原始需要删除的软件包列表
            success_count (int): 成功删除的数量
            failed_files (List[str]): 失败的文件列表

        Returns:
            str: 格式化的结果消息
        """
        result_msg = f"成功删除了 {success_count}/{len(to_delete)} 个旧版本"
        if failed_files:
            result_msg += f"\n\n删除失败的文件:\n" + "\n".join(failed_files[:3])
            if len(failed_files) > 3:
                result_msg += f"\n...等共 {len(failed_files)} 个文件"

        return result_msg
