import logging
import sys
import importlib.util
import os
import inspect

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def import_module_from_file(file_path, module_name):
    """从文件导入模块"""
    try:
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None:
            logging.error(f"无法从{file_path}创建模块规范")
            return None
            
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module
    except Exception as e:
        logging.error(f"从{file_path}导入模块时出错: {e}")
        return None

# 测试函数 - 使用Market Analyzer实现
def test_market_analyzer_format():
    logging.info("测试market_analyzer.py中的_format_price实现")
    from market_analyzer import MarketAnalyzer
    from market_data import MarketData
    
    md = MarketData()
    analyzer = MarketAnalyzer(md)
    
    test_values = [0.0, 0.00000001, 0.0003278, 0.003278, 0.03278, 0.3278, 3.278, 32.78, 327.8, 3278.0]
    results = []
    
    for val in test_values:
        formatted = analyzer._format_price(val)
        results.append(f"{val} -> {formatted}")
        
    return results

# 测试函数 - 使用Bot实现
def test_bot_format():
    logging.info("测试bot.py中的_format_price实现")
    bot_module = import_module_from_file("bot.py", "bot")
    
    if not hasattr(bot_module, "_format_price"):
        logging.error("bot.py中找不到_format_price函数")
        
        # 尝试找出bot中使用的市场分析器类
        for attr_name in dir(bot_module):
            attr = getattr(bot_module, attr_name)
            if attr_name == "MarketAnalyzer" and hasattr(attr, "_format_price"):
                logging.info(f"在bot.py中找到了MarketAnalyzer类")
                
                # 检查是否需要实例化
                if inspect.isclass(attr):
                    logging.info("MarketAnalyzer是一个类，需要实例化")
                    
                    # 查找Market Analyzer的依赖
                    market_data_class = None
                    for name in dir(bot_module):
                        obj = getattr(bot_module, name)
                        if name == "MarketData" and inspect.isclass(obj):
                            market_data_class = obj
                            break
                    
                    if market_data_class:
                        try:
                            # 创建MarketData实例
                            market_data = market_data_class()
                            # 创建MarketAnalyzer实例
                            analyzer_instance = attr(market_data)
                            
                            # 测试_format_price
                            test_values = [0.0, 0.00000001, 0.0003278, 0.003278, 0.03278, 0.3278, 3.278, 32.78, 327.8, 3278.0]
                            results = []
                            
                            for val in test_values:
                                try:
                                    formatted = analyzer_instance._format_price(val)
                                    results.append(f"{val} -> {formatted}")
                                except Exception as e:
                                    logging.error(f"调用_format_price出错: {e}")
                                    results.append(f"{val} -> 错误: {e}")
                                    
                            return results
                        except Exception as e:
                            logging.error(f"实例化MarketAnalyzer时出错: {e}")
                            return None
                    else:
                        logging.error("找不到MarketData类，无法实例化MarketAnalyzer")
                        return None
                else:
                    logging.info("MarketAnalyzer是一个实例，直接使用")
                    # 使用这个对象的_format_price
                    test_values = [0.0, 0.00000001, 0.0003278, 0.003278, 0.03278, 0.3278, 3.278, 32.78, 327.8, 3278.0]
                    results = []
                    
                    for val in test_values:
                        try:
                            formatted = attr._format_price(val)
                            results.append(f"{val} -> {formatted}")
                        except Exception as e:
                            logging.error(f"调用_format_price出错: {e}")
                            results.append(f"{val} -> 错误: {e}")
                            
                    return results
            elif hasattr(attr, "_format_price"):
                logging.info(f"在bot.py的{attr_name}对象中找到了_format_price")
                # 使用这个对象的_format_price
                test_values = [0.0, 0.00000001, 0.0003278, 0.003278, 0.03278, 0.3278, 3.278, 32.78, 327.8, 3278.0]
                results = []
                
                for val in test_values:
                    try:
                        formatted = attr._format_price(val)
                        results.append(f"{val} -> {formatted}")
                    except Exception as e:
                        logging.error(f"调用_format_price出错: {e}")
                        results.append(f"{val} -> 错误: {e}")
                        
                return results
        
        logging.error("在bot.py中没有找到任何包含_format_price的对象")
        return None
    else:
        # 直接使用bot模块中的_format_price
        format_price_func = getattr(bot_module, "_format_price")
        
        test_values = [0.0, 0.00000001, 0.0003278, 0.003278, 0.03278, 0.3278, 3.278, 32.78, 327.8, 3278.0]
        results = []
        
        for val in test_values:
            try:
                formatted = format_price_func(val)
                results.append(f"{val} -> {formatted}")
            except Exception as e:
                logging.error(f"调用_format_price出错: {e}")
                results.append(f"{val} -> 错误: {e}")
                
        return results

# 运行测试
if __name__ == "__main__":
    print("测试MarketAnalyzer的_format_price:")
    market_analyzer_results = test_market_analyzer_format()
    for result in market_analyzer_results:
        print(result)
        
    print("\n测试Bot的_format_price:")
    bot_results = test_bot_format()
    if bot_results:
        for result in bot_results:
            print(result)
    else:
        print("无法测试Bot的_format_price函数") 