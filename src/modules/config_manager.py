import os
import json
from pathlib import Path

class ConfigManager:
    """配置管理器"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.init_config()
        return cls._instance
    
    def init_config(self):
        """初始化配置"""
        self.ensure_config_dir()
        self.init_log_config()
    
    def ensure_config_dir(self):
        """确保配置目录存在"""
        self.config_dir = os.path.expanduser('~/.config/arch-zst-backup')
        os.makedirs(self.config_dir, exist_ok=True)
        return self.config_dir
    
    def load_config(self):
        """加载主配置文件"""
        config_path = os.path.join(self.config_dir, 'config.json')
        
        # 确保配置文件存在
        if not os.path.exists(config_path):
            with open(config_path, 'w') as f:
                json.dump({'logLevel': 'INFO'}, f, indent=2)
            return {'logLevel': 'INFO'}
        
        try:
            with open(config_path) as f:
                config = json.load(f)
                # 确保logLevel有默认值
                if 'logLevel' not in config:
                    config['logLevel'] = 'INFO'
                return config
        except Exception:
            return {'logLevel': 'INFO'}
    
    def init_log_config(self):
        """初始化日志配置文件"""
        log_config_path = os.path.join(self.config_dir, 'log_config.json')
        
        if not os.path.exists(log_config_path):
            default_log_config = {
                'level': 'INFO',
                'file': None,
                'maxSize': 1048576  # 1MB
            }
            with open(log_config_path, 'w') as f:
                json.dump(default_log_config, f, indent=2)

    def save_config(self, config):
        """保存主配置文件"""
        try:
            config_path = os.path.join(self.config_dir, 'config.json')
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            return True
        except Exception:
            return False

# 单例配置管理器实例
config_manager = ConfigManager()