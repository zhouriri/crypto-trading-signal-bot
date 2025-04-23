"""
交易信号机器人核心模块

该模块包含机器人的核心功能，如初始化、配置加载和主要处理逻辑
"""

from .bot_initializer import initialize_bot
from .config_loader import load_config

__all__ = ['initialize_bot', 'load_config'] 