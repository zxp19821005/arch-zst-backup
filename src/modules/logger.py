from datetime import datetime

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
            cls._instance = super().__new__(cls)
            cls._instance._level = 1  # 默认INFO级别
            cls._instance._print = print
            cls._initialized = True
            print(f"初始化Logger单例实例，ID: {id(cls._instance)}")
        return cls._instance
    
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
            self._print(f"[DEBUG] {datetime.now()} - {msg}")

    def info(self, msg: str):
        """记录普通信息"""
        if self.should_log('INFO'):
            self._print(f"[INFO] {datetime.now()} - {msg}")

    def success(self, msg: str):
        """记录成功信息"""
        if self.should_log('SUCCESS'):
            self._print(f"[SUCCESS] {datetime.now()} - {msg}")

    def warning(self, msg: str):
        """记录警告信息"""
        if self.should_log('WARNING'):
            self._print(f"[WARNING] {datetime.now()} - {msg}")

    def error(self, msg: str):
        """记录错误信息"""
        if self.should_log('ERROR'):
            self._print(f"[ERROR] {datetime.now()} - {msg}")

# 创建全局日志实例
log = Logger()