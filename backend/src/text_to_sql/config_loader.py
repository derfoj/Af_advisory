import yaml
import os
from typing import Dict, Any

class ConfigLoader:
    _instance = None
    _config: Dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigLoader, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self):
        config_path = os.path.join(os.path.dirname(__file__), 'config', 'llm_config.yaml')
        try:
            with open(config_path, 'r') as file:
                self._config = yaml.safe_load(file)
        except FileNotFoundError:
            print(f"Error: Configuration file not found at {config_path}")
            self._config = {}
        except yaml.YAMLError as exc:
            print(f"Error parsing YAML file: {exc}")
            self._config = {}

    @property
    def config(self) -> Dict[str, Any]:
        return self._config

# Global instance
GLOBAL_CONFIG = ConfigLoader().config