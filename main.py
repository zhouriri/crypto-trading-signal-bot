from market_data import MarketData
from market_analyzer import MarketAnalyzer
import logging
import sys

def main():
    try:
        # 获取命令行参数
        if len(sys.argv) > 1:
            symbol = sys.argv[1]
        else:
            symbol = 'BTC'  # 默认分析BTC
            
        # 初始化市场数据对象
        market_data = MarketData()
        
        # 初始化分析器
        analyzer = MarketAnalyzer(market_data)
        
        # 分析指定币种的市场数据
        report = analyzer.analyze_market(symbol, timeframe='1h')
        
        # 打印分析报告
        print(report)
        
    except Exception as e:
        logging.error(f"程序运行出错: {str(e)}")
        raise

if __name__ == "__main__":
    main() 