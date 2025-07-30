from datetime import datetime, timedelta
import os
import threading
import gzip
import shutil
import glob
from pathlib import Path
from enum import Enum

class LogLevelColors(Enum):
    """日志级别颜色枚举"""
    DEBUG = ("#6C7A89", "DEBUG")    # 灰色
    INFO = ("#3498DB", "INFO")      # 蓝色
    SUCCESS = ("#2ECC71", "SUCCESS") # 绿色
    WARNING = ("#F39C12", "WARNING") # 橙色
    ERROR = ("#E74C3C", "ERROR")     # 红色

class Logger:
    """日志记录器(严格单例模式)"""

    _instance = None
    _initialized = False

    LEVELS = {
        'DEBUG': 0,
        'INFO': 1,
        'SUCCESS': 1,
        'WARNING': 2,
        'ERROR': 3
    }

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            cls._instance._level = 1  # 默认INFO级别
            cls._instance._print = print
            cls._instance._log_file = None
            cls._instance._file_lock = threading.Lock()
            cls._initialized = True
            print(f"初始化Logger单例实例，ID: {id(cls._instance)}")
        return cls._instance

    def __init__(self):
        # 使用类变量确保只初始化一次
        if not Logger._initialized:
            self._level = 1  # 默认INFO级别
            self._print = print
            Logger._initialized = True

    def set_log_file(self, file_path):
        """设置日志文件路径"""
        with self._file_lock:
            if self._log_file and self._log_file != file_path:
                self._log_file.close()
            
            # 确保日志目录存在
            log_dir = os.path.dirname(file_path)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
            
            self._log_file = open(file_path, "a", encoding="utf-8")
            self._log_file.write(f"\n=== 日志会话开始: {datetime.now()} ===\n")
            self._log_file.flush()
    
    def set_level(self, level_name: str):
        """设置日志级别"""
        level = self.LEVELS.get(level_name.upper())
        if level is not None and self._level != level:
            self._level = level
            print(f"设置日志级别为: {level_name} (数值: {level})")
            print(f"Logger实例ID: {id(self)}")
            print(f"当前所有日志级别: {self.LEVELS}")

    def should_log(self, level_name: str) -> bool:
        """检查是否应该记录指定级别的日志"""
        level = self.LEVELS.get(level_name.upper())
        if level is None:
            return False
        # 只有当消息级别 >= 设置的日志级别时才记录
        return level >= self._level

    def debug(self, msg: str):
        """记录调试信息"""
        if self.should_log('DEBUG'):
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            plain_msg = f"[DEBUG] {timestamp} - {msg}"
            color = LogLevelColors.DEBUG.value[0]
            html_msg = f'<span style="color:{color}">[DEBUG] {timestamp} - {msg}</span>'
            self._print(plain_msg)
            self._write_to_file(plain_msg)
            return html_msg

    def info(self, msg: str):
        """记录普通信息"""
        if self.should_log('INFO'):
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            plain_msg = f"[INFO] {timestamp} - {msg}"
            color = LogLevelColors.INFO.value[0]
            html_msg = f'<span style="color:{color}">[INFO] {timestamp} - {msg}</span>'
            self._print(plain_msg)
            self._write_to_file(plain_msg)
            return html_msg

    def success(self, msg: str):
        """记录成功信息"""
        if self.should_log('SUCCESS'):
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            plain_msg = f"[SUCCESS] {timestamp} - {msg}"
            color = LogLevelColors.SUCCESS.value[0]
            html_msg = f'<span style="color:{color}">[SUCCESS] {timestamp} - {msg}</span>'
            self._print(plain_msg)
            self._write_to_file(plain_msg)
            return html_msg

    def warning(self, msg: str):
        """记录警告信息"""
        if self.should_log('WARNING'):
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            plain_msg = f"[WARNING] {timestamp} - {msg}"
            color = LogLevelColors.WARNING.value[0]
            html_msg = f'<span style="color:{color}">[WARNING] {timestamp} - {msg}</span>'
            self._print(plain_msg)
            self._write_to_file(plain_msg)
            return html_msg

    def error(self, msg: str):
        """记录错误信息"""
        if self.should_log('ERROR'):
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            plain_msg = f"[ERROR] {timestamp} - {msg}"
            color = LogLevelColors.ERROR.value[0]
            html_msg = f'<span style="color:{color}">[ERROR] {timestamp} - {msg}</span>'
            self._print(plain_msg)
            self._write_to_file(plain_msg)
            return html_msg
    
    def _write_to_file(self, log_msg):
        """将日志消息写入文件"""
        with self._file_lock:
            if self._log_file:
                try:
                    self._log_file.write(log_msg + "\n")
                    self._log_file.flush()
                except Exception as e:
                    # 文件写入失败时回退到控制台输出
                    print(f"写入日志文件失败: {e}")

    def manage_logs(self, retention_days=30):
        """管理日志文件，压缩大文件并删除过期日志
        
        Args:
            retention_days (int): 日志保留天数，默认30天
        """
        if not self._log_file:
            return
            
        try:
            # 获取日志文件所在目录
            log_dir = os.path.dirname(self._log_file.name)
            if not log_dir or not os.path.exists(log_dir):
                return
                
            # 当前时间
            now = datetime.now()
            
            # 1. 检查并压缩大文件
            self._compress_large_logs(log_dir)
            
            # 2. 删除过期日志
            self._delete_old_logs(log_dir, now, retention_days)
            
            self.info(f"日志管理完成，保留天数: {retention_days}")
        except Exception as e:
            self.error(f"日志管理失败: {e}")
    
    def _compress_large_logs(self, log_dir):
        """压缩大于10MB的日志文件
        
        Args:
            log_dir (str): 日志目录路径
        """
        # 10MB大小限制
        max_size = 10 * 1024 * 1024  # 10MB
        
        # 查找所有.log文件
        log_files = glob.glob(os.path.join(log_dir, "*.log"))
        
        for log_file in log_files:
            try:
                # 检查文件大小
                file_size = os.path.getsize(log_file)
                if file_size > max_size:
                    # 创建压缩文件名
                    gz_file = f"{log_file}.{datetime.now().strftime('%Y%m%d%H%M%S')}.gz"
                    
                    # 压缩文件
                    with open(log_file, 'rb') as f_in:
                        with gzip.open(gz_file, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    
                    # 清空原文件
                    with open(log_file, 'w', encoding="utf-8") as f:
                        f.write(f"=== 日志文件已压缩，原文件大小: {file_size} bytes ===\n")
                        f.write(f"=== 压缩文件: {os.path.basename(gz_file)} ===\n")
                        f.write(f"=== 压缩时间: {datetime.now()} ===\n\n")
                    
                    self.info(f"已压缩日志文件: {os.path.basename(log_file)} -> {os.path.basename(gz_file)}")
            except Exception as e:
                self.error(f"压缩日志文件失败 {log_file}: {e}")
    
    def _delete_old_logs(self, log_dir, now, retention_days):
        """删除超过保留天数的日志文件
        
        Args:
            log_dir (str): 日志目录路径
            now (datetime): 当前时间
            retention_days (int): 保留天数
        """
        # 计算截止日期
        cutoff_date = now - timedelta(days=retention_days)
        
        # 查找所有日志文件（包括压缩文件）
        log_patterns = [
            os.path.join(log_dir, "*.log"),
            os.path.join(log_dir, "*.log.*.gz")
        ]
        
        for pattern in log_patterns:
            for log_file in glob.glob(pattern):
                try:
                    # 获取文件修改时间
                    file_mtime = datetime.fromtimestamp(os.path.getmtime(log_file))
                    
                    # 如果文件超过保留天数，删除它
                    if file_mtime < cutoff_date:
                        os.remove(log_file)
                        self.info(f"已删除过期日志文件: {os.path.basename(log_file)}")
                except Exception as e:
                    self.error(f"删除日志文件失败 {log_file}: {e}")

# 创建全局日志实例
log = Logger()
