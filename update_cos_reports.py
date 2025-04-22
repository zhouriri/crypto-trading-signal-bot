from market_data import MarketData
from market_analyzer import MarketAnalyzer
import logging

logging.basicConfig(level=logging.INFO)
md = MarketData()
analyzer = MarketAnalyzer(md)

# 分析COS的中期策略
result = analyzer.analyze_market('COS', 'mid')
output_file = 'results/COS_mid_result.txt'
with open(output_file, 'w') as f:
    f.write(result)
print('COS中期分析已更新')

# 分析COS的长期策略
result = analyzer.analyze_market('COS', 'long')
output_file = 'results/COS_long_result.txt'
with open(output_file, 'w') as f:
    f.write(result)
print('COS长期分析已更新') 