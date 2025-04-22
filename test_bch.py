from market_data import MarketData
from market_analyzer import MarketAnalyzer
import logging

# 设置日志等级
logging.basicConfig(level=logging.INFO)

# 创建市场数据对象
md = MarketData()
# 创建分析器
analyzer = MarketAnalyzer(md)

# 分析BCH
result = analyzer.analyze_market('BCH', 'short')

# 打印分析结果
print(result) 