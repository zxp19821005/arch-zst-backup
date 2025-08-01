"""
公共工具方法
"""
import json
import logging
from pathlib import Path
from modules.config_manager import config_manager
from modules.version_comparator import version_comparator

log = logging.getLogger(__name__)

def force_rescan_and_update_status_bar(instance, count_duplicate_method=None, count_backupable_method=None):
    """
    强制重新扫描并更新状态栏
    :param instance: 当前页面实例
    :param count_duplicate_method: 计算重复软件包数量的方法
    :param count_backupable_method: 计算可备份软件包数量的方法
    """
    if not hasattr(instance, 'packages') or not instance.packages:
        return

    # 临时保存当前的data_loaded状态
    original_data_loaded = instance.data_loaded
    instance.data_loaded = False  # 设置为False以强制刷新

    # 根据实例类型调用不同的扫描方法
    if hasattr(instance, 'scan_backup_dir'):
        instance.scan_backup_dir()
    elif hasattr(instance, 'scan_cache_dirs'):
        instance.scan_cache_dirs()

    instance.data_loaded = original_data_loaded  # 恢复原始状态

    duplicate_count = count_duplicate_method() if count_duplicate_method else 0
    backupable_count = count_backupable_method() if count_backupable_method else 0

    if instance.parent() and hasattr(instance.parent(), 'parent') and instance.parent().parent():
        main_window = instance.parent().parent()
        if hasattr(main_window, 'status_bar') and len(instance.packages) > 0:
            message = f"共 {len(instance.packages)} 个软件包，其中有 {duplicate_count} 个重复软件包"
            if count_backupable_method:
                message += f"，有 {backupable_count} 个软件包可以备份"
            main_window.status_bar.show_permanent_message(message)


def update_status_bar(instance, count_duplicate_method=None, count_backupable_method=None):
    """
    仅更新状态栏
    :param instance: 当前页面实例
    :param count_duplicate_method: 计算重复软件包数量的方法
    :param count_backupable_method: 计算可备份软件包数量的方法
    """
    if not hasattr(instance, 'packages') or not instance.packages:
        return

    duplicate_count = count_duplicate_method() if count_duplicate_method else 0
    backupable_count = count_backupable_method() if count_backupable_method else 0

    if instance.parent() and hasattr(instance.parent(), 'parent') and instance.parent().parent():
        main_window = instance.parent().parent()
        if hasattr(main_window, 'status_bar') and len(instance.packages) > 0:
            message = f"共 {len(instance.packages)} 个软件包，其中有 {duplicate_count} 个重复软件包"
            if count_backupable_method:
                message += f"，有 {backupable_count} 个软件包可以备份"
            main_window.status_bar.show_permanent_message(message)


def count_duplicate_packages(packages):
    """
    计算重复软件包数量
    :param packages: 软件包列表
    :return: 重复软件包数量
    """
    if not packages:
        return 0

    # 按名称和架构分组软件包
    grouped = {}
    for pkg in packages:
        key = (pkg['pkgname'], pkg['arch'])
        grouped.setdefault(key, []).append(pkg)

    # 计算重复软件包数量
    duplicate_count = 0
    for pkgs in grouped.values():
        if len(pkgs) > 1:
            duplicate_count += len(pkgs) - 1  # 每组中除了最新版本外，其余都算作重复

    return duplicate_count


def count_backupable_packages(packages):
    """
    计算可备份软件包数量
    :param packages: 软件包列表
    :return: 可备份软件包数量
    """
    if not packages:
        return 0

    # 加载备份目录中已有的软件包信息
    config_dir = Path(config_manager.config_dir)
    existing_packages_file = config_dir / "existing_packages.json"
    existing_packages = []

    if existing_packages_file.exists():
        try:
            with open(existing_packages_file, 'r', encoding='utf-8') as f:
                existing_packages = json.load(f)
        except Exception as e:
            log.error(f"加载已有软件包列表失败: {str(e)}")
            return 0

    # 创建已有软件包的名称-版本映射
    existing_map = {}
    for pkg in existing_packages:
        # 确保必要的字段存在，支持不同的字段名
        pkg_name = pkg.get('pkgname') or pkg.get('name')
        pkg_arch = pkg.get('arch')

        if not pkg_name or not pkg_arch:
            log.warning(f"跳过格式不正确的软件包: {pkg}")
            continue

        key = (pkg_name, pkg_arch)

        # 确保版本字段存在，支持不同的字段名
        pkg_version = pkg.get('pkgver') or pkg.get('version')
        pkg_rel = pkg.get('relver') or pkg.get('pkgrel')
        pkg_epoch = pkg.get('epoch') or '0'

        if not pkg_version or not pkg_rel:
            log.warning(f"软件包 {pkg_name} 缺少版本信息，跳过")
            continue

        # 创建标准化的软件包对象用于版本比较
        pkg_for_compare = {
            'pkgname': pkg_name,
            'pkgver': pkg_version,
            'relver': pkg_rel,
            'epoch': pkg_epoch,
            'arch': pkg_arch
        }

        if key not in existing_map or version_comparator.compare_versions(pkg_for_compare, existing_map[key]['compare_obj']) > 0:
            existing_map[key] = {
                'original': pkg,
                'compare_obj': pkg_for_compare
            }

    # 计算可备份的软件包数量
    backupable_count = 0
    for pkg in packages:
        # 确保必要的字段存在
        pkg_name = pkg.get('pkgname')
        pkg_arch = pkg.get('arch')

        if not pkg_name or not pkg_arch:
            continue

        key = (pkg_name, pkg_arch)

        # 如果软件包不在备份目录中，或者版本比备份目录中的更新，则可以备份
        if key not in existing_map:
            backupable_count += 1
        else:
            # 确保版本字段存在
            pkg_version = pkg.get('pkgver')
            pkg_rel = pkg.get('relver')
            pkg_epoch = pkg.get('epoch') or '0'

            if not pkg_version or not pkg_rel:
                continue

            # 创建标准化的软件包对象用于版本比较
            pkg_for_compare = {
                'pkgname': pkg_name,
                'pkgver': pkg_version,
                'relver': pkg_rel,
                'epoch': pkg_epoch,
                'arch': pkg_arch
            }

            if version_comparator.compare_versions(pkg_for_compare, existing_map[key]['compare_obj']) > 0:
                backupable_count += 1

    return backupable_count
