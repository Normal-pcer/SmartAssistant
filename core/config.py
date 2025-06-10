import json
import os
from typing import Dict, Any
from core.ai_client import AIModel

DEFAULT_CONFIG_PATH = os.path.expanduser("~/.smart_assistant/config.json")

class InvalidConfigError(Exception):
    """配置文件格式错误"""
    def __init__(self, message: str) -> None:
        super().__init__(message)

class Config:
    """存储配置文件中的信息"""

    models = list[AIModel]()
    current_model_index = 0

    def __init__(self, config_path: str = DEFAULT_CONFIG_PATH) -> None:
        self.config_path = config_path
        self.load()
    
    def __del__(self) -> None:
        self.save()

    def load(self) -> None:
        try:
            with open(self.config_path, "r", encoding="UTF-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            return # 使用默认配置
        
        try:
            self.models = [AIModel(**model) for model in data["models"]]
            self.current_model_index = int(data["current_model_index"])
        except KeyError as e:
            raise InvalidConfigError(f"配置文件格式错误: {e}")

    def save(self) -> None:
        data: Dict[str, Any] = {
            "models": [model.to_dict() for model in self.models],
            "current_model_index": self.current_model_index
        }
        with open(self.config_path, "w", encoding="UTF-8") as f:
            json.dump(data, f, indent=4)
