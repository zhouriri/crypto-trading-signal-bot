#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import logging
from dotenv import load_dotenv
from market_data import MarketData
from market_analyzer import MarketAnalyzer

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("test_strategies.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def test_strategies():
    """测试不同策略模式的结果"""
    logger.info("开始测试不同货币和策略的分析结果")
    
    # 创建市场数据和分析器实例
    market_data = MarketData()
    market_analyzer = MarketAnalyzer(market_data)
    
    # 要测试的货币列表
    symbols = ['BTC', 'BCH', 'COS', 'FIL']
    
    # 要测试的策略列表
    strategies = ['short', 'mid', 'long']
    
    # 存储测试结果
    results = {}
    
    # 逐个测试每种货币的每种策略
    for symbol in symbols:
        results[symbol] = {}
        
        for strategy in strategies:
            logger.info(f"测试 {symbol} 的 {strategy} 策略...")
            
            # 获取分析结果
            try:
                report = market_analyzer.analyze_market(symbol, strategy)
                results[symbol][strategy] = report
                
                # 将结果保存到文件
                result_file = f"results/{symbol}_{strategy}_result.txt"
                os.makedirs(os.path.dirname(result_file), exist_ok=True)
                
                with open(result_file, 'w') as f:
                    f.write(report or "无结果")
                
                logger.info(f"已将 {symbol} 的 {strategy} 策略结果保存到 {result_file}")
                
                # 如果有结果，输出摘要
                if report:
                    # 提取关键信息
                    summary_lines = []
                    
                    # 查找策略方向
                    if "推荐方向" in report:
                        direction_line = next((line for line in report.split('\n') if "推荐方向" in line), None)
                        if direction_line:
                            summary_lines.append(direction_line.strip())
                    
                    # 查找RSI
                    if "RSI" in report:
                        rsi_line = next((line for line in report.split('\n') if "RSI" in line and "：" in line), None)
                        if rsi_line:
                            summary_lines.append(rsi_line.strip())
                    
                    # 查找成交量
                    if "成交量" in report:
                        volume_line = next((line for line in report.split('\n') if "成交量" in line and "变化" in line), None)
                        if volume_line:
                            summary_lines.append(volume_line.strip())
                    
                    # 打印摘要
                    if summary_lines:
                        logger.info(f"{symbol} {strategy} 策略摘要:")
                        for line in summary_lines:
                            logger.info(f"  {line}")
                    else:
                        logger.info(f"{symbol} {strategy} 策略结果无法提取摘要")
                else:
                    logger.warning(f"{symbol} 的 {strategy} 策略未返回结果")
            
            except Exception as e:
                logger.error(f"测试 {symbol} 的 {strategy} 策略时出错: {str(e)}")
                results[symbol][strategy] = f"错误: {str(e)}"
            
            # 在测试之间稍作暂停，避免API过载
            time.sleep(2)
    
    logger.info("所有测试完成")
    return results

if __name__ == "__main__":
    try:
        load_dotenv()  # 加载环境变量
        test_results = test_strategies()
        logger.info(f"成功完成 {len(test_results)} 个货币的策略测试")
    except Exception as e:
        logger.error(f"测试过程中发生错误: {str(e)}") 