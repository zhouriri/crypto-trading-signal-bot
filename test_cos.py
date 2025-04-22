from market_data import MarketData
from market_analyzer import MarketAnalyzer
import logging

# 设置日志等级
logging.basicConfig(level=logging.INFO)

# 创建市场数据对象
md = MarketData()
# 创建分析器
analyzer = MarketAnalyzer(md)

# 分析COS
result = analyzer.analyze_market('COS', 'short')

# 打印分析结果
print(result)

# 单独测试格式化函数
print("\n\n测试格式化函数:")
test_values = [0.0, 0.00000001, 0.0003278, 0.003278, 0.03278, 0.3278, 3.278, 32.78, 327.8, 3278.0]
for val in test_values:
    formatted = analyzer._format_price(val)
    print(f"原始值: {val} -> 格式化后: {formatted}") 