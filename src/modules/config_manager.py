import os
import json
from pathlib import Path

class ConfigManager:
    """配置管理器"""

    _instance = None

    # 中英文字段名映射表
    FIELD_MAPPING = {
        "名称": "name",
        "版本": "version",
        "发布号": "release",
        "架构": "arch",
        "位置": "location"
    }

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.init_config()
        return cls._instance

    def init_config(self):
        """初始化配置"""
        self.ensure_config_dir()

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
                json.dump({
                    'logLevel': 'INFO',
                    'backupDir': '/path/to/backup',
                    'displaySettings': {
                        'epoch': {'alignment': 'center'},
                        'name': {'alignment': 'left'},
                        'version': {'alignment': 'left'},
                        'release': {'alignment': 'left'},
                        'arch': {'alignment': 'left'},
                        'location': {'alignment': 'left'}
                    }
                }, f, indent=2)
            return {
                'logLevel': 'INFO',
                'backupDir': '/path/to/backup',
                'displaySettings': {
                    'epoch': {'alignment': 'center'},
                    'name': {'alignment': 'left'},
                    'version': {'alignment': 'left'},
                    'release': {'alignment': 'left'},
                    'arch': {'alignment': 'left'},
                    'location': {'alignment': 'left'}
                }
            }

        try:
            with open(config_path) as f:
                config = json.load(f)
                # 确保logLevel有默认值
                if 'logLevel' not in config:
                    config['logLevel'] = 'INFO'

                # 确保backupDir有默认值
                if 'backupDir' not in config:
                    config['backupDir'] = '/path/to/backup'

                # 保持英文字段名，不转换为中文
                # 注意：这里不再进行字段名转换，保持配置文件中使用英文列名

                return config
        except Exception:
            return {'logLevel': 'INFO', 'backupDir': '/path/to/backup'}

    def save_config(self, config):
        """保存主配置文件"""
        try:
            config_path = os.path.join(self.config_dir, 'config.json')

            # 深拷贝配置以避免修改原始数据
            config_copy = json.loads(json.dumps(config))

            # 保持英文字段名，不进行转换
            # 注意：这里不再进行字段名转换，保持配置文件中使用英文列名

            with open(config_path, 'w') as f:
                json.dump(config_copy, f, indent=2)
            return True
        except Exception:
            return False

# 单例配置管理器实例
config_manager = ConfigManager()
