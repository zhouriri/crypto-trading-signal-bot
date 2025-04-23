"""
配置加载模块

负责从环境变量或配置文件中加载机器人的配置
"""

import os
import json
import logging
from dotenv import load_dotenv
from typing import Dict, Any, Optional

# 配置日志格式
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    加载配置信息
    
    Args:
        config_path: 配置文件路径，如果不提供则尝试从默认位置和环境变量加载
        
    Returns:
        包含配置信息的字典
    """
    # 加载环境变量
    load_dotenv()
    
    config = {
        "telegram": {
            "api_token": os.getenv("TELEGRAM_BOT_TOKEN"),
            "chat_id": os.getenv("TELEGRAM_CHAT_ID"),
            "proxy": {
                "enabled": bool(os.getenv("HTTP_PROXY")),
                "http_proxy": os.getenv("HTTP_PROXY"),
                "https_proxy": os.getenv("HTTPS_PROXY")
            }
        },
        "market_data": {
            "cmc_api_key": os.getenv("CMC_API_KEY"),
            "default_symbol": "BTC",
            "default_strategy": "short"
        },
        "logging": {
            "level": os.getenv("LOG_LEVEL", "INFO"),
            "file": "bot_output.log"
        }
    }
    
    # 如果提供了配置文件路径，尝试从文件加载配置
    if config_path and os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                file_config = json.load(f)
                # 递归合并配置
                _merge_configs(config, file_config)
            logger.info(f"已从 {config_path} 加载配置")
        except Exception as e:
            logger.error(f"加载配置文件失败: {str(e)}")
    
    # 检查必要的配置项
    if not config["telegram"]["api_token"]:
        logger.warning("未找到 Telegram Bot Token，请检查环境变量或配置文件")
    
    return config

def _merge_configs(base: Dict[str, Any], override: Dict[str, Any]) -> None:
    """
    递归合并两个配置字典
    
    Args:
        base: 基础配置字典(将被修改)
        override: 覆盖配置字典
    """
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _merge_configs(base[key], value)
        else:
            base[key] = value 