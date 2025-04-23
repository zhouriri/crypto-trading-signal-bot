#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交易信号机器人主入口

此文件是新的入口点，使用面向对象的设计结构
"""

import os
import sys
import logging
import argparse
from typing import Optional

# 导入机器人相关类
from bots import TradingBot, TelegramTradingBot, SimpleTelegramBot, BotManager

def setup_logging() -> None:
    """
    设置基本日志记录
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("trading_bot.log"),
            logging.StreamHandler()
        ]
    )

def parse_arguments():
    """
    解析命令行参数
    
    Returns:
        解析后的参数
    """
    parser = argparse.ArgumentParser(description='交易信号机器人')
    parser.add_argument('--type', '-t', choices=['main', 'simple'], default='main',
                      help='机器人类型：main (完整版) 或 simple (简化版)')
    parser.add_argument('--config', '-c', type=str, default=None,
                      help='配置文件路径')
    parser.add_argument('--external', '-e', action='store_true',
                      help='使用外部进程启动机器人')
    
    return parser.parse_args()

def main() -> None:
    """
    主函数
    """
    # 设置日志
    setup_logging()
    logger = logging.getLogger("main")
    
    try:
        # 解析命令行参数
        args = parse_arguments()
        
        # 创建机器人管理器
        manager = BotManager(args.config)
        
        # 根据参数决定启动方式
        if args.external:
            # 使用外部进程启动机器人
            logger.info(f"使用外部进程启动 {args.type} 类型的机器人...")
            success = manager.run_bot_externally(args.type)
        else:
            # 在当前进程中启动机器人
            logger.info(f"在当前进程中启动 {args.type} 类型的机器人...")
            success = manager.start_bot(args.type)
        
        if success:
            logger.info("机器人启动成功")
        else:
            logger.error("机器人启动失败")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("接收到用户中断，正在退出...")
    except Exception as e:
        logger.error(f"启动机器人时出错: {str(e)}")
        logging.exception("错误详情")
        sys.exit(1)

if __name__ == "__main__":
    main() 