"""
交易机器人基类

定义所有交易机器人的共同接口和基本功能
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Tuple

class TradingBot(ABC):
    """
    交易机器人基类
    
    提供交易机器人的基本接口和通用功能
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化交易机器人
        
        Args:
            config: 机器人配置信息
        """
        self.config = config
        self.logger = self._setup_logger()
        self.initialized = False
        self.running = False
        self.strategy = config.get('default_strategy', 'short')
        
        self.logger.info(f"交易机器人基类初始化，策略: {self.strategy}")
    
    def _setup_logger(self) -> logging.Logger:
        """
        设置日志
        
        Returns:
            配置好的日志记录器
        """
        logger_name = self.__class__.__name__
        logger = logging.getLogger(logger_name)
        
        # 避免重复设置处理器
        if not logger.handlers:
            log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            formatter = logging.Formatter(log_format)
            
            # 获取日志文件名称，默认使用类名
            log_file = self.config.get('log_file', f"{logger_name.lower()}.log")
            
            # 添加文件处理器
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            
            # 添加控制台处理器
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
            
            # 设置日志级别
            log_level = self.config.get('log_level', 'INFO')
            logger.setLevel(getattr(logging, log_level, logging.INFO))
        
        return logger
    
    @abstractmethod
    def initialize(self) -> bool:
        """
        初始化机器人
        
        Returns:
            初始化是否成功
        """
        self.logger.info("开始初始化交易机器人...")
        self.initialized = True
        return True
    
    @abstractmethod
    def run(self) -> None:
        """
        运行机器人
        """
        if not self.initialized:
            self.logger.error("机器人尚未初始化，无法运行")
            raise RuntimeError("机器人尚未初始化，无法运行")
        
        self.running = True
        self.logger.info("机器人开始运行")
    
    @abstractmethod
    def stop(self) -> None:
        """
        停止机器人
        """
        self.running = False
        self.logger.info("机器人已停止")
    
    @abstractmethod
    def analyze(self, symbol: str, strategy: Optional[str] = None) -> str:
        """
        分析市场数据
        
        Args:
            symbol: 交易对符号
            strategy: 策略类型，如果不提供则使用默认策略
            
        Returns:
            分析报告文本
        """
        pass
    
    def change_strategy(self, strategy: str) -> bool:
        """
        更改分析策略
        
        Args:
            strategy: 新策略名称
            
        Returns:
            更改是否成功
        """
        valid_strategies = ['short', 'mid', 'long']
        if strategy not in valid_strategies:
            self.logger.warning(f"无效的策略: {strategy}, 有效策略: {valid_strategies}")
            return False
        
        self.strategy = strategy
        self.logger.info(f"已切换到策略: {strategy}")
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取机器人状态信息
        
        Returns:
            包含状态信息的字典
        """
        return {
            'initialized': self.initialized,
            'running': self.running,
            'strategy': self.strategy,
            'config': self.config
        }
    
    def __str__(self) -> str:
        """
        返回机器人的字符串表示
        
        Returns:
            机器人的描述字符串
        """
        status = "运行中" if self.running else "未运行"
        return f"{self.__class__.__name__} [状态: {status}, 策略: {self.strategy}]" 