import os
import json
from pathlib import Path

# 默认配置常量
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_BACKUP_DIR = "/path/to/backup"
DEFAULT_DISPLAY_SETTINGS = {
    'epoch': {'alignment': 'center'},
    'pkgname': {'alignment': 'center'},
    'pkgver': {'alignment': 'center'},
    'relver': {'alignment': 'center'},
    'arch': {'alignment': 'center'},
    'location': {'alignment': 'left'}
}

# 有效的日志级别
VALID_LOG_LEVELS = ["DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR"]

# 有效的对齐方式
VALID_ALIGNMENTS = ["left", "center", "right"]

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
        pass
        self.config_dir = os.path.expanduser('~/.config/arch-zst-backup')
        os.makedirs(self.config_dir, exist_ok=True)
        return self.config_dir

    def load_config(self):
        """加载主配置文件"""
        config_path = os.path.join(self.config_dir, 'config.json')

        # 确保配置文件存在
        if not os.path.exists(config_path):
            default_config = {
                'logLevel': DEFAULT_LOG_LEVEL,
                'backupDir': DEFAULT_BACKUP_DIR,
                'displaySettings': DEFAULT_DISPLAY_SETTINGS
            }
            with open(config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
            return default_config.copy()

        try:
            with open(config_path) as f:
                config = json.load(f)
                
                # 确保必要配置项存在，不存在则使用默认值
                if 'logLevel' not in config:
                    config['logLevel'] = DEFAULT_LOG_LEVEL
                    
                if 'backupDir' not in config:
                    config['backupDir'] = DEFAULT_BACKUP_DIR
                    
                if 'displaySettings' not in config:
                    config['displaySettings'] = DEFAULT_DISPLAY_SETTINGS.copy()
                
                # 验证配置值
                self._validate_config(config)
                
                return config
        except json.JSONDecodeError as e:
            print(f"配置文件格式错误: {e}")
            return {
                'logLevel': DEFAULT_LOG_LEVEL,
                'backupDir': DEFAULT_BACKUP_DIR,
                'displaySettings': DEFAULT_DISPLAY_SETTINGS.copy()
            }
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            return {
                'logLevel': DEFAULT_LOG_LEVEL,
                'backupDir': DEFAULT_BACKUP_DIR,
                'displaySettings': DEFAULT_DISPLAY_SETTINGS.copy()
            }

    def _validate_config(self, config):
        """验证配置值的有效性
        
        Args:
            config (dict): 要验证的配置字典
            
        Raises:
            ValueError: 当配置值无效时
        """
        # 验证日志级别
        if 'logLevel' in config and config['logLevel'] not in VALID_LOG_LEVELS:
            print(f"警告: 无效的日志级别 '{config['logLevel']}', 将使用默认值 '{DEFAULT_LOG_LEVEL}'")
            config['logLevel'] = DEFAULT_LOG_LEVEL
            
        # 验证备份目录
        if 'backupDir' in config:
            backup_dir = config['backupDir']
            if not isinstance(backup_dir, str) or not backup_dir.strip():
                print(f"警告: 无效的备份目录 '{backup_dir}', 将使用默认值 '{DEFAULT_BACKUP_DIR}'")
                config['backupDir'] = DEFAULT_BACKUP_DIR
        
        # 验证显示设置
        if 'displaySettings' in config:
            display_settings = config['displaySettings']
            if not isinstance(display_settings, dict):
                print("警告: displaySettings 不是有效的字典，将使用默认值")
                config['displaySettings'] = DEFAULT_DISPLAY_SETTINGS.copy()
            else:
                # 验证每个列的对齐方式
                for column, settings in display_settings.items():
                    if not isinstance(settings, dict) or 'alignment' not in settings:
                        print(f"警告: 列 '{column}' 的设置无效，将使用默认值")
                        settings['alignment'] = DEFAULT_DISPLAY_SETTINGS.get(column, {}).get('alignment', 'center')
                    elif settings['alignment'] not in VALID_ALIGNMENTS:
                        print(f"警告: 列 '{column}' 的对齐方式 '{settings['alignment']}' 无效，将使用默认值")
                        settings['alignment'] = DEFAULT_DISPLAY_SETTINGS.get(column, {}).get('alignment', 'center')
    
    def save_config(self, config):
        """保存主配置文件"""
        try:
            config_path = os.path.join(self.config_dir, 'config.json')

            # 深拷贝配置以避免修改原始数据
            config_copy = json.loads(json.dumps(config))

            # 验证配置
            self._validate_config(config_copy)

            with open(config_path, 'w') as f:
                json.dump(config_copy, f, indent=2)
            return True
        except Exception as e:
            print(f"保存配置失败: {e}")
            return False

# 单例配置管理器实例
config_manager = ConfigManager()
