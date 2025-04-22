import logging
from market_data import MarketData

# 配置日志
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_long_strategy():
    """测试long策略类型"""
    try:
        # 创建MarketData实例
        market_data = MarketData('BTCUSDT')
        
        # 测试get_market_analysis方法
        logger.info("测试get_market_analysis方法，使用'long'策略类型...")
        analysis_data = market_data.get_market_analysis('BTC', 'long')
        
        if analysis_data:
            logger.info("成功获取'long'策略的市场分析数据")
            # 打印K线数据的时间框架
            if 'klines' in analysis_data:
                timeframes = list(analysis_data['klines'].keys())
                logger.info(f"获取的时间框架: {timeframes}")
            else:
                logger.error("分析数据中没有K线数据")
        else:
            logger.error("获取'long'策略的市场分析数据失败")
    except Exception as e:
        logger.error(f"测试过程中发生异常: {str(e)}")

if __name__ == "__main__":
    test_long_strategy() 