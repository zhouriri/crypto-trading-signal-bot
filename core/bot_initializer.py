"""
机器人初始化模块

负责初始化机器人所需的各种组件和服务
"""

import logging
import sys
from typing import Optional, Dict, Any
from market_data import MarketData
from market_analyzer import MarketAnalyzer
from .config_loader import load_config

# 配置日志
logger = logging.getLogger(__name__)

def setup_logging(config: Dict[str, Any]) -> None:
    """
    设置日志记录
    
    Args:
        config: 配置字典
    """
    log_level = getattr(logging, config["logging"]["level"], logging.INFO)
    log_file = config["logging"]["file"]
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    logger.debug("日志系统初始化完成")

def setup_environment(config: Dict[str, Any]) -> None:
    """
    设置环境变量和代理
    
    Args:
        config: 配置字典
    """
    # 设置代理（如果启用）
    if config["telegram"]["proxy"]["enabled"]:
        import os
        http_proxy = config["telegram"]["proxy"]["http_proxy"]
        https_proxy = config["telegram"]["proxy"]["https_proxy"]
        
        if http_proxy:
            os.environ["HTTP_PROXY"] = http_proxy
            logger.debug(f"已设置 HTTP 代理: {http_proxy}")
        
        if https_proxy:
            os.environ["HTTPS_PROXY"] = https_proxy
            logger.debug(f"已设置 HTTPS 代理: {https_proxy}")

def run_analyzer(config: Dict[str, Any], symbol: Optional[str] = None) -> None:
    """
    运行市场分析器
    
    Args:
        config: 配置字典
        symbol: 要分析的交易对符号，如果不提供则使用默认值
    """
    try:
        # 使用命令行参数或默认值
        if not symbol:
            symbol = config["market_data"]["default_symbol"]
        
        # 初始化市场数据对象
        market_data = MarketData()
        
        # 初始化分析器
        analyzer = MarketAnalyzer(market_data)
        
        # 分析指定币种的市场数据
        strategy = config["market_data"]["default_strategy"]
        report = analyzer.analyze_market(symbol, strategy)
        
        # 打印分析报告
        print(report)
        
    except Exception as e:
        logger.error(f"分析器运行出错: {str(e)}")
        raise

def initialize_bot(config_path: Optional[str] = None) -> None:
    """
    初始化机器人并运行
    
    Args:
        config_path: 配置文件路径
    """
    try:
        # 加载配置
        config = load_config(config_path)
        
        # 设置日志
        setup_logging(config)
        
        # 设置环境变量和代理
        setup_environment(config)
        
        # 获取命令行参数
        symbol = None
        if len(sys.argv) > 1:
            symbol = sys.argv[1]
        
        # 运行分析器
        run_analyzer(config, symbol)
        
        logger.info("分析完成")
        
    except Exception as e:
        logger.error(f"初始化机器人出错: {str(e)}")
        logger.debug("错误详情:", exc_info=True)
        sys.exit(1) 