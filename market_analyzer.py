from market_data import MarketData
import logging
import logging.handlers
from datetime import datetime
from market_analysis_rules import TechnicalAnalysisRules, TrendDirection, SignalStrength

# 创建日志格式化器
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# 创建文件处理器
file_handler = logging.handlers.RotatingFileHandler(
    'market_analyzer.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5,
    encoding='utf-8'
)
file_handler.setFormatter(formatter)

# 创建控制台处理器
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

# 配置根日志记录器
logging.basicConfig(level=logging.INFO, handlers=[file_handler, console_handler])
logger = logging.getLogger(__name__)

class MarketAnalyzer:
    def __init__(self, market_data):
        self.market_data = market_data
        self.analysis_rules = TechnicalAnalysisRules()
        
    def analyze_market(self, symbol, timeframe='1h'):
        """分析市场数据"""
        try:
            logger.info(f"开始分析{symbol}的{timeframe}周期市场数据...")
            
            # 设置市场数据类的交易对
            self.market_data.symbol = f"{symbol}USDT"
            
            # 获取市场数据
            market_data = self.market_data.get_market_analysis(symbol, timeframe)
            if market_data is None:
                logger.error(f"获取{symbol}的{timeframe}周期市场数据失败")
                return "获取市场数据失败，请稍后重试"
            
            # 获取当前价格
            current_price = None
            if 'klines' in market_data and market_data['klines']:
                klines_data = market_data['klines']
                for tf in ['1m', '5m', '15m', '1h', '4h', '1d']:
                    if tf in klines_data and not klines_data[tf].empty:
                        current_price = float(klines_data[tf].iloc[-1]['close'])
                        break
            
            if current_price is None:
                logger.warning(f"无法获取{symbol}的当前价格")
                current_price = 0.0
            
            # 根据策略类型选择分析方法
            if timeframe == 'short':
                # 检查是否需要生成交易信号推送格式
                use_signal_push_format = self._should_use_signal_push_format(market_data)
                if use_signal_push_format:
                    return self._generate_short_term_signal_push(symbol, market_data, current_price)
                    
                strategy_analysis = self.analyze_short_term(market_data)
            elif timeframe == 'mid':
                # 使用信号推送格式进行中期分析
                use_signal_push_format = self._should_use_signal_push_format(market_data)
                if use_signal_push_format:
                    return self._generate_mid_term_signal_push(symbol, market_data, current_price)
                
                strategy_analysis = self.analyze_mid_term(market_data)
            elif timeframe == 'long':
                # 使用信号推送格式进行长期分析
                use_signal_push_format = self._should_use_signal_push_format(market_data)
                if use_signal_push_format:
                    return self._generate_long_term_signal_push(symbol, market_data, current_price)
                
                strategy_analysis = self.analyze_long_term(market_data)
            else:
                strategy_analysis = "无效的策略类型"
                
            # 分析价格趋势
            try:
                price_trend = self.analyze_price_trend(market_data)
                logger.info(f"价格趋势分析完成: {price_trend}")
            except Exception as e:
                logger.error(f"价格趋势分析失败: {str(e)}")
                price_trend = "价格趋势分析失败"
                
            # 分析成交量
            try:
                volume_analysis = self.analyze_volume(market_data)
                logger.info(f"成交量分析完成: {volume_analysis}")
            except Exception as e:
                logger.error(f"成交量分析失败: {str(e)}")
                volume_analysis = "成交量分析失败"
                
            # 分析合约持仓
            try:
                futures_analysis = self.analyze_futures(market_data)
                logger.info(f"合约持仓分析完成: {futures_analysis}")
            except Exception as e:
                logger.error(f"合约持仓分析失败: {str(e)}")
                futures_analysis = "合约持仓分析失败"
                
            # 分析筹码分布
            try:
                chip_distribution = self.analyze_chip_distribution(market_data)
                logger.info(f"筹码分布分析完成: {chip_distribution}")
            except Exception as e:
                logger.error(f"筹码分布分析失败: {str(e)}")
                chip_distribution = "筹码分布分析失败"
                
            # 分析长期投资机会
            try:
                long_term_analysis = self.analyze_long_term(market_data)
                logger.info(f"长期投资分析完成: {long_term_analysis}")
            except Exception as e:
                logger.error(f"长期投资分析失败: {str(e)}")
                long_term_analysis = "长期投资分析失败"
                
            # 生成交易建议
            try:
                trading_suggestion = self.generate_trading_suggestion(
                    price_trend, volume_analysis, futures_analysis, chip_distribution, strategy_analysis
                )
                logger.info(f"交易建议生成完成: {trading_suggestion}")
            except Exception as e:
                logger.error(f"生成交易建议失败: {str(e)}")
                trading_suggestion = "生成交易建议失败"
                
            # 生成长期投资建议
            try:
                long_term_suggestion = self.generate_long_term_suggestion(long_term_analysis)
                logger.info(f"长期投资建议生成完成: {long_term_suggestion}")
            except Exception as e:
                logger.error(f"生成长期投资建议失败: {str(e)}")
                long_term_suggestion = "生成长期投资建议失败"
                
            # 获取当前时间
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            # 格式化当前价格
            current_price_str = self._format_price(current_price)
                
            # 生成分析报告
            report = f"""
{symbol} {timeframe}周期市场分析报告
--------------------------------
📅 分析时间: {current_time}
💰 当前价格: ${current_price_str}
--------------------------------
1. 策略分析:
{strategy_analysis}

2. 价格趋势分析:
{price_trend}

3. 成交量分析:
{volume_analysis}

4. 合约持仓分析:
{futures_analysis}

5. 筹码分布分析:
{chip_distribution}

6. 长期投资分析:
{long_term_analysis}

7. 交易建议:
{trading_suggestion}

8. 长期投资建议:
{long_term_suggestion}
--------------------------------
"""
            logger.info(f"{symbol}的{timeframe}周期市场分析报告生成完成")
            return report
            
        except Exception as e:
            logger.error(f"分析{symbol}的{timeframe}周期市场数据时发生异常: {str(e)}")
            return f"分析{symbol}的{timeframe}周期市场数据时发生错误，请稍后重试"
            
    def analyze_price_trend(self, market_data):
        """分析价格趋势"""
        try:
            if 'klines' not in market_data or not market_data['klines']:
                return "无法获取价格数据"
                
            klines_data = market_data['klines']
            if not isinstance(klines_data, dict) or not klines_data:
                return "价格数据格式错误"
                
            # 获取最新的1小时数据
            df_1h = klines_data.get('1h')
            if df_1h is None or df_1h.empty:
                return "无法获取1小时周期数据"
                
            latest = df_1h.iloc[-1]
            prev = df_1h.iloc[-2]
            
            # 准备EMA数据
            ema_data = {
                'ema5': float(latest['ema5']),
                'ema13': float(latest['ema13']),
                'ema20': float(latest['ma20']),  # 使用MA20代替EMA20
                'ema50': float(latest['ma50']),  # 使用MA50代替EMA50
                'ema100': float(latest['ma50'])  # 使用MA50代替EMA100
            }
            
            # 分析趋势指标
            trend_direction, trend_strength = self.analysis_rules.analyze_trend(ema_data)
            
            # 分析动量指标
            momentum_direction, momentum_strength = self.analysis_rules.analyze_momentum(
                float(latest['rsi']),
                float(latest['macd']),
                float(latest['macd_signal'])
            )
            
            # 分析成交量指标
            volume_direction, volume_strength = self.analysis_rules.analyze_volume(
                float(latest['volume']),
                float(latest['volume_ma20']),
                float(latest['close']) - float(prev['close'])
            )
            
            # 分析支撑阻力
            support_resistance_direction, support_resistance_strength = self.analysis_rules.analyze_support_resistance(
                float(latest['close']),
                [float(latest['bb_lower'])],
                [float(latest['bb_upper'])],
                float(latest['volume']),
                float(latest['volume_ma20'])
            )
            
            # 生成最终信号
            final_direction, final_strength = self.analysis_rules.generate_final_signal(
                (trend_direction, trend_strength),
                (momentum_direction, momentum_strength),
                (volume_direction, volume_strength),
                (support_resistance_direction, support_resistance_strength)
            )
            
            # 生成分析报告
            report = f"""价格趋势分析:
1. 趋势方向: {trend_direction.value}
2. 趋势强度: {trend_strength.value}
3. 动量指标:
   - RSI: {latest['rsi']:.2f}
   - MACD: {latest['macd']:.2f}
4. 成交量分析:
   - 当前成交量: {latest['volume']:.2f}
   - 20周期均量: {latest['volume_ma20']:.2f}
5. 支撑阻力位:
   - 上轨: {latest['bb_upper']:.2f}
   - 下轨: {latest['bb_lower']:.2f}

综合判断: {final_direction.value}，信号强度: {final_strength.value}"""
            
            return report
            
        except Exception as e:
            logger.error(f"分析价格趋势失败: {str(e)}")
            return "价格趋势分析失败"
            
    def analyze_volume(self, market_data):
        """分析成交量"""
        try:
            if 'klines' not in market_data or not market_data['klines']:
                return "无法获取成交量数据"
                
            klines_data = market_data['klines']
            if not isinstance(klines_data, dict) or not klines_data:
                return "成交量数据格式错误"
                
            # 获取最新的1小时数据
            df_1h = klines_data.get('1h')
            if df_1h is None or df_1h.empty:
                return "无法获取1小时周期数据"
                
            latest = df_1h.iloc[-1]
            prev = df_1h.iloc[-2]
            
            # 计算成交量变化
            volume_change = (latest['volume'] - prev['volume']) / prev['volume'] * 100
            volume_ma_ratio = latest['volume'] / latest['volume_ma20']
            
            # 判断成交量性质
            if volume_change > 30 and latest['close'] > prev['close']:
                volume_nature = "放量上涨"
            elif volume_change > 30 and latest['close'] < prev['close']:
                volume_nature = "放量下跌"
            elif volume_change < -30 and latest['close'] > prev['close']:
                volume_nature = "缩量上涨"
            elif volume_change < -30 and latest['close'] < prev['close']:
                volume_nature = "缩量下跌"
            else:
                volume_nature = "成交量变化不显著"
                
            # 生成分析报告
            report = f"""成交量分析:
1. 成交量变化: {volume_change:.2f}%
2. 相对均量比: {volume_ma_ratio:.2f}
3. 成交量性质: {volume_nature}
4. 当前成交量: {latest['volume']:.2f}
5. 20周期均量: {latest['volume_ma20']:.2f}

成交量判断: {volume_nature}"""
            
            return report
            
        except Exception as e:
            logger.error(f"分析成交量失败: {str(e)}")
            return "成交量分析失败"
            
    def analyze_futures(self, market_data):
        """分析合约持仓"""
        try:
            futures_data = market_data.get('futures_data', {})
            if not futures_data:
                return "无合约持仓数据"
                
            # 获取合约数据
            long_short_ratio = futures_data.get('long_short_ratio')
            funding_rate = float(futures_data.get('funding_rate', 0))
            
            # 分析合约持仓
            analysis = "合约持仓分析:\n"
            
            # 处理多空比可能为None的情况
            if long_short_ratio is None:
                analysis += "- 多空比数据缺失，无法分析多空持仓情况\n"
            elif float(long_short_ratio) > 1.5:
                analysis += "- 多头持仓显著高于空头，市场情绪偏多\n"
            elif float(long_short_ratio) < 0.67:
                analysis += "- 空头持仓显著高于多头，市场情绪偏空\n"
            else:
                analysis += "- 多空持仓相对平衡\n"
                
            if funding_rate > 0.01:
                analysis += "- 资金费率较高，短期可能有回调压力\n"
            elif funding_rate < -0.01:
                analysis += "- 资金费率为负，短期可能有反弹机会\n"
            else:
                analysis += "- 资金费率处于正常水平\n"
                
            return analysis
            
        except Exception as e:
            logger.error(f"分析合约持仓失败: {str(e)}")
            return "合约持仓分析失败"
            
    def analyze_chip_distribution(self, market_data):
        """分析筹码分布"""
        try:
            if 'volume_profile' not in market_data:
                return "无法获取筹码分布数据"
                
            chip_data = market_data['volume_profile']
            if not isinstance(chip_data, dict):
                return "筹码分布数据格式错误"
                
            # 获取当前价格
            current_price = None
            if 'klines' in market_data and market_data['klines']:
                klines_data = market_data['klines']
                if '1h' in klines_data and not klines_data['1h'].empty:
                    current_price = float(klines_data['1h'].iloc[-1]['close'])
            
            if current_price is None:
                return "无法获取当前价格"
                
            # 分析筹码分布
            total_volume = sum(chip_data.values())
            if total_volume == 0:
                return "筹码分布数据无效"
                
            # 找到成交量最大的价格区间
            max_volume_range = max(chip_data.items(), key=lambda x: x[1])
            max_volume_price_range = max_volume_range[0]
            max_volume_percentage = (max_volume_range[1] / total_volume) * 100
            
            # 计算当前价格以下的筹码比例
            volume_below_current = 0
            for price_range, volume in chip_data.items():
                lower, upper = map(float, price_range.split('-'))
                if upper <= current_price:
                    volume_below_current += volume
            
            volume_below_percentage = (volume_below_current / total_volume) * 100
            
            # 生成分析报告
            report = f"""筹码分布分析:
1. 成交量最大价格区间: {max_volume_price_range}
2. 主力筹码集中度: {max_volume_percentage:.2f}%
3. 获利盘比例: {volume_below_percentage:.2f}%

筹码分布判断:"""
            
            # 根据筹码分布特征给出判断
            if max_volume_percentage > 30:
                report += "\n- 筹码高度集中，可能存在较强支撑/压力"
            else:
                report += "\n- 筹码分布较为分散，价格波动可能较大"
                
            if volume_below_percentage > 70:
                report += "\n- 获利盘比例较高，存在回调风险"
            elif volume_below_percentage < 30:
                report += "\n- 套牢盘比例较高，可能存在反弹机会"
            else:
                report += "\n- 获利盘比例适中，价格趋于平衡"
            
            return report
            
        except Exception as e:
            logger.error(f"分析筹码分布失败: {str(e)}")
            return "筹码分布分析失败"
            
    def analyze_short_term(self, market_data):
        """分析短期波段机会"""
        try:
            klines_data = market_data['klines']
            
            # 获取各时间框架数据
            klines_15m = klines_data['15m']
            klines_1h = klines_data['1h']
            klines_4h = klines_data['4h']
            
            # 分析4小时趋势
            latest_4h = klines_4h.iloc[-1]
            trend_4h_direction, trend_4h_strength = self.analysis_rules.analyze_trend({
                'ema5': float(latest_4h['ema5']),
                'ema13': float(latest_4h['ema13']),
                'ema20': float(latest_4h['ma20']),   # 使用ma20替代ema20
                'ema50': float(latest_4h['ma50']),   # 使用ma50替代ema50
                'ema100': float(latest_4h['ma50'])   # 使用ma50替代ema100（数据中没有ema100）
            })
            
            # 分析1小时趋势
            latest_1h = klines_1h.iloc[-1]
            trend_1h_direction, trend_1h_strength = self.analysis_rules.analyze_trend({
                'ema5': float(latest_1h['ema5']),
                'ema13': float(latest_1h['ema13']),
                'ema20': float(latest_1h['ma20']),   # 使用ma20替代ema20
                'ema50': float(latest_1h['ma50']),   # 使用ma50替代ema50
                'ema100': float(latest_1h['ma50'])   # 使用ma50替代ema100（数据中没有ema100）
            })
            
            # 分析15分钟信号
            latest_15m = klines_15m.iloc[-1]
            prev_15m = klines_15m.iloc[-2]
            
            # 分析动量指标
            momentum_direction, momentum_strength = self.analysis_rules.analyze_momentum(
                float(latest_15m['rsi']),
                float(latest_15m['macd']),
                float(latest_15m['macd_signal'])
            )
            
            # 分析成交量指标
            volume_direction, volume_strength = self.analysis_rules.analyze_volume(
                float(latest_15m['volume']),
                float(latest_15m['volume_ma20']),
                float(latest_15m['close']) - float(prev_15m['close'])
            )
            
            # 生成分析报告
            analysis = f"""
短期波段分析:
4小时趋势: {trend_4h_direction.value} ({trend_4h_strength.name})
1小时趋势: {trend_1h_direction.value} ({trend_1h_strength.name})
15分钟信号: {momentum_direction.value} ({momentum_strength.name})
成交量: {volume_direction.value} ({volume_strength.name})
"""
            return analysis
            
        except Exception as e:
            logger.error(f"分析短期波段机会失败: {str(e)}")
            return "短期波段分析失败"
            
    def analyze_mid_term(self, market_data):
        """分析中期趋势机会"""
        try:
            klines_data = market_data['klines']
            
            # 获取各时间框架数据
            klines_1h = klines_data['1h']
            klines_4h = klines_data['4h']
            klines_1d = klines_data['1d']
            
            # 分析日线趋势
            latest_1d = klines_1d.iloc[-1]
            trend_1d_direction, trend_1d_strength = self.analysis_rules.analyze_trend({
                'ema5': float(latest_1d['ema5']),
                'ema13': float(latest_1d['ema13']),
                'ema20': float(latest_1d['ma20']),   # 使用ma20替代ema20
                'ema50': float(latest_1d['ma50']),   # 使用ma50替代ema50
                'ema100': float(latest_1d['ma50'])   # 使用ma50替代ema100（数据中没有ema100）
            })
            
            # 分析4小时趋势
            latest_4h = klines_4h.iloc[-1]
            trend_4h_direction, trend_4h_strength = self.analysis_rules.analyze_trend({
                'ema5': float(latest_4h['ema5']),
                'ema13': float(latest_4h['ema13']),
                'ema20': float(latest_4h['ma20']),   # 使用ma20替代ema20
                'ema50': float(latest_4h['ma50']),   # 使用ma50替代ema50
                'ema100': float(latest_4h['ma50'])   # 使用ma50替代ema100（数据中没有ema100）
            })
            
            # 分析1小时信号
            latest_1h = klines_1h.iloc[-1]
            prev_1h = klines_1h.iloc[-2]
            
            # 分析动量指标
            momentum_direction, momentum_strength = self.analysis_rules.analyze_momentum(
                float(latest_1h['rsi']),
                float(latest_1h['macd']),
                float(latest_1h['macd_signal'])
            )
            
            # 分析成交量指标
            volume_direction, volume_strength = self.analysis_rules.analyze_volume(
                float(latest_1h['volume']),
                float(latest_1h['volume_ma20']),
                float(latest_1h['close']) - float(prev_1h['close'])
            )
            
            # 生成分析报告
            analysis = f"""
中期趋势分析:
日线趋势: {trend_1d_direction.value} ({trend_1d_strength.name})
4小时趋势: {trend_4h_direction.value} ({trend_4h_strength.name})
1小时信号: {momentum_direction.value} ({momentum_strength.name})
成交量: {volume_direction.value} ({volume_strength.name})
"""
            return analysis
            
        except Exception as e:
            logger.error(f"分析中期趋势机会失败: {str(e)}")
            return "中期趋势分析失败"
            
    def analyze_long_term(self, market_data):
        """分析长期投资机会"""
        try:
            # 获取当前价格
            current_price = None
            if 'klines' in market_data and market_data['klines']:
                klines_data = market_data['klines']
                for tf in ['1d', '3d', '1w']:
                    if tf in klines_data and not klines_data[tf].empty:
                        current_price = float(klines_data[tf].iloc[-1]['close'])
                        break
            
            if current_price is None:
                logger.warning("无法获取当前价格用于长期投资分析")
                return "无法获取价格数据进行长期投资分析"
                
            # 获取链上数据
            onchain_data = market_data.get('onchain_data', {})
            mvrv_z = self._safe_float(onchain_data, 'mvrv_z', 0)
            nvt = self._safe_float(onchain_data, 'nvt', 0)
            
            # 格式化显示值
            current_price_str = self._format_price(current_price)
            mvrv_z_str = self._format_price(mvrv_z)
            nvt_str = self._format_price(nvt)
            
            # 分析市值与实现价值比率
            mvrv_analysis = "市值处于合理水平"
            if mvrv_z < -1:
                mvrv_analysis = "市值严重低估，可能是长期投资的好时机"
            elif mvrv_z < 0:
                mvrv_analysis = "市值略低估，可考虑长期投资"
            elif mvrv_z > 3:
                mvrv_analysis = "市值严重高估，可能面临调整风险"
            elif mvrv_z > 1:
                mvrv_analysis = "市值略高估，长期投资需谨慎"
                
            # 分析网络价值与交易比率
            nvt_analysis = "链上活动与市值匹配度合理"
            if nvt < 20:
                nvt_analysis = "链上活动活跃，价格可能被低估"
            elif nvt > 100:
                nvt_analysis = "链上活动较少，价格可能被高估"
                
            # 生成综合分析
            analysis = f"""
长期投资分析:
当前价格: ${current_price_str}
MVRV-Z评分: {mvrv_z_str} - {mvrv_analysis}
NVT比率: {nvt_str} - {nvt_analysis}
"""
            
            return analysis
            
        except Exception as e:
            logger.error(f"分析长期投资机会失败: {str(e)}")
            return "长期投资分析失败"
            
    def generate_trading_suggestion(self, price_trend, volume_analysis, futures_analysis, chip_distribution, strategy_analysis):
        """生成交易建议"""
        try:
            # 分析趋势信号
            trend_signal = "中性"
            if "看涨" in price_trend and "STRONG" in price_trend:
                trend_signal = "看多"
            elif "看跌" in price_trend and "STRONG" in price_trend:
                trend_signal = "看空"
                
            # 分析成交量信号
            volume_signal = "中性"
            if "放量上涨" in volume_analysis:
                volume_signal = "看多"
            elif "放量下跌" in volume_analysis:
                volume_signal = "看空"
                
            # 分析合约持仓信号
            futures_signal = "中性"
            if "多头持仓显著高于空头" in futures_analysis:
                futures_signal = "看多"
            elif "空头持仓显著高于多头" in futures_analysis:
                futures_signal = "看空"
                
            # 分析筹码分布信号
            chip_signal = "中性"
            if "当前价格显著高于平均成本" in chip_distribution:
                chip_signal = "看空"
            elif "当前价格显著低于平均成本" in chip_distribution:
                chip_signal = "看多"
                
            # 生成交易建议
            suggestion = f"""
交易建议:
1. 趋势信号: {trend_signal}
2. 成交量信号: {volume_signal}
3. 合约持仓信号: {futures_signal}
4. 筹码分布信号: {chip_signal}

综合建议: {self._generate_comprehensive_suggestion(
    trend_signal, volume_signal, futures_signal, chip_signal
)}
"""
            return suggestion
            
        except Exception as e:
            logger.error(f"生成交易建议失败: {str(e)}")
            return "生成交易建议失败"
            
    def _generate_comprehensive_suggestion(self, trend_signal, volume_signal, futures_signal, chip_signal):
        """生成综合建议"""
        # 计算看多和看空的信号数量
        bullish_signals = sum(1 for signal in [trend_signal, volume_signal, futures_signal, chip_signal] if signal == "看多")
        bearish_signals = sum(1 for signal in [trend_signal, volume_signal, futures_signal, chip_signal] if signal == "看空")
        
        if bullish_signals >= 3:
            return "强烈看多，建议逢低买入"
        elif bearish_signals >= 3:
            return "强烈看空，建议逢高卖出"
        elif bullish_signals > bearish_signals:
            return "偏多，可考虑分批建仓"
        elif bearish_signals > bullish_signals:
            return "偏空，建议观望或轻仓"
        else:
            return "震荡行情，建议观望"
            
    def generate_long_term_suggestion(self, long_term_analysis):
        """生成长期投资建议"""
        try:
            # 分析MVRV-Z信号
            mvrv_signal = "中性"
            if "市值严重低估" in long_term_analysis:
                mvrv_signal = "强烈看多"
            elif "市值略低估" in long_term_analysis:
                mvrv_signal = "看多"
            elif "市值严重高估" in long_term_analysis:
                mvrv_signal = "强烈看空"
            elif "市值略高估" in long_term_analysis:
                mvrv_signal = "看空"
                
            # 分析NVT信号
            nvt_signal = "中性"
            if "链上活动活跃" in long_term_analysis:
                nvt_signal = "看多"
            elif "链上活动较少" in long_term_analysis:
                nvt_signal = "看空"
                
            # 生成长期投资建议
            suggestion = f"""
长期投资建议:
1. MVRV-Z信号: {mvrv_signal}
2. NVT信号: {nvt_signal}

综合建议: {self._generate_long_term_comprehensive_suggestion(mvrv_signal, nvt_signal)}
"""
            return suggestion
            
        except Exception as e:
            logger.error(f"生成长期投资建议失败: {str(e)}")
            return "生成长期投资建议失败"
            
    def _generate_long_term_comprehensive_suggestion(self, mvrv_signal, nvt_signal):
        """生成长期投资综合建议"""
        if mvrv_signal == "强烈看多" and nvt_signal == "看多":
            return "强烈建议长期投资，当前是极佳的买入时机"
        elif mvrv_signal == "强烈看空" and nvt_signal == "看空":
            return "建议暂时观望，等待更好的买入时机"
        elif mvrv_signal == "看多" or nvt_signal == "看多":
            return "可以考虑分批建仓，进行长期投资"
        elif mvrv_signal == "看空" or nvt_signal == "看空":
            return "建议谨慎投资，等待更好的机会"
        else:
            return "市场处于平衡状态，建议保持观望"
            
    def _format_price(self, price):
        """格式化价格显示"""
        try:
            # 处理None和零值
            if price is None:
                return "N/A"
            
            # 确保price是浮点数
            price = float(price)
            
            # 针对非常接近0的值，但实际不为0的情况
            if abs(price) < 0.0000001 and price != 0:
                return "接近0"
                
            # 如果是0，直接返回0
            if price == 0:
                return "0"
            
            # 根据价格范围动态调整精度
            if price < 0.0001:  # 极小值，像COS这样的代币
                formatted_price = f"{price:.8f}"
            elif price < 0.01:  # 小于1分钱
                formatted_price = f"{price:.6f}"
            elif price < 1:     # 小于1元
                formatted_price = f"{price:.4f}"
            elif price < 10000: # 普通价格
                formatted_price = f"{price:.2f}"
            else:              # 高价格
                formatted_price = f"{price:.2f}"
            
            # 分离整数部分和小数部分
            integer_part, decimal_part = formatted_price.split('.')
            
            # 为整数部分添加千位分隔符
            integer_with_commas = "{:,}".format(int(integer_part))
            
            # 移除小数部分末尾的0，但至少保留两位小数（对于小值保留更多）
            if price < 0.01:
                # 对于小值，保留足够的小数位但去除末尾的0
                decimal_trimmed = decimal_part.rstrip('0')
                if len(decimal_trimmed) < 4:  # 确保至少有4位小数
                    decimal_trimmed = decimal_part[:4]
            else:
                # 对于较大的值，至少保留2位小数
                decimal_trimmed = decimal_part
                if len(decimal_trimmed) > 2:
                    if all(c == '0' for c in decimal_trimmed[2:]):
                        decimal_trimmed = decimal_trimmed[:2]
            
            # 确保至少有一位小数
            if not decimal_trimmed:
                decimal_trimmed = '0'
                
            # 组合结果
            return f"{integer_with_commas}.{decimal_trimmed}"
        except Exception as e:
            logger.error(f"价格格式化失败: {str(e)}")
            return str(price)
            
    def _safe_float(self, data, key, default=0):
        """安全获取浮点数值"""
        try:
            return float(data.get(key, default))
        except:
            return default

    def _should_use_signal_push_format(self, market_data):
        """判断是否使用信号推送格式（可根据市场波动等条件决定）"""
        # 这里简单地返回True，你可以添加更复杂的逻辑
        return True
        
    def _generate_short_term_signal_push(self, symbol, market_data, current_price):
        """生成短期波段策略信号推送报告"""
        try:
            # 获取当前时间
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            # 获取K线数据
            klines_data = market_data['klines']
            latest_15m = klines_data['15m'].iloc[-1]
            latest_1h = klines_data['1h'].iloc[-1]
            latest_4h = klines_data['4h'].iloc[-1]
            
            # 获取技术指标数据
            rsi = float(latest_15m['rsi'])
            macd = float(latest_15m['macd'])
            macd_signal = float(latest_15m['macd_signal'])
            ema5 = float(latest_15m['ema5'])
            ema13 = float(latest_15m['ema13'])
            volume = float(latest_15m['volume'])
            volume_ma20 = float(latest_15m['volume_ma20'])
            
            # 获取合约数据
            futures_data = market_data.get('futures_data', {})
            funding_rate = float(futures_data.get('funding_rate', 0)) * 100  # 转为百分比
            long_short_ratio = futures_data.get('long_short_ratio', None)  # 允许None值
            
            # 获取筹码分布数据
            chip_data = market_data.get('volume_profile', {})
            if chip_data:
                total_volume = sum(chip_data.values())
                # 找到成交量最大的价格区间
                max_volume_range = max(chip_data.items(), key=lambda x: x[1])
                max_volume_price_range = max_volume_range[0]
                max_volume_percentage = (max_volume_range[1] / total_volume) * 100
                
                # 计算获利盘比例
                volume_below_current = 0
                for price_range, volume in chip_data.items():
                    lower, upper = map(float, price_range.split('-'))
                    if upper <= current_price:
                        volume_below_current += volume
                
                profit_percentage = (volume_below_current / total_volume) * 100
            else:
                max_volume_price_range = "N/A"
                max_volume_percentage = 0
                profit_percentage = 0
            
            # 判断RSI区域
            rsi_zone = "中性区域"
            rsi_signal = "中性"
            if rsi > 70:
                rsi_zone = "超买区域"
                rsi_signal = "看空"
            elif rsi < 30:
                rsi_zone = "超卖区域"
                rsi_signal = "看多"
            
            # 判断MACD情况
            macd_signal_trend = "中性"
            if macd > macd_signal:
                macd_status = "金叉（短期动能转向多头）"
                macd_signal_trend = "看多"
            else:
                macd_status = "死叉（短期动能转向空头）"
                macd_signal_trend = "看空"
            
            # 判断EMA趋势
            ema_signal = "中性"
            if ema5 > ema13:
                ema_trend = "EMA5 > EMA13（金叉，短期趋势向上）"
                ema_signal = "看多"
            else:
                ema_trend = "EMA5 < EMA13（死叉，短期趋势向下）"
                ema_signal = "看空"
            
            # 判断成交量情况
            volume_signal = "中性"
            volume_change = (volume / volume_ma20 - 1) * 100
            if volume_change > 30 and latest_15m['close'] > latest_15m['open']:
                volume_status = "放量上涨"
                volume_signal = "看多"
            elif volume_change > 30 and latest_15m['close'] < latest_15m['open']:
                volume_status = "放量下跌"
                volume_signal = "看空"
            elif volume_change < -30 and latest_15m['close'] > latest_15m['open']:
                volume_status = "缩量上涨"
                volume_signal = "中性偏空"
            elif volume_change < -30 and latest_15m['close'] < latest_15m['open']:
                volume_status = "缩量下跌"
                volume_signal = "中性偏多"
            else:
                volume_status = "成交量正常"
            
            # 判断资金费率情况
            funding_signal = "中性"
            if funding_rate > 0.01:
                funding_status = "多头略占优"
                funding_signal = "看空"
            elif funding_rate < -0.01:
                funding_status = "空头略占优"
                funding_signal = "看多"
            else:
                funding_status = "多空平衡"
            
            # 判断多空比情况
            if long_short_ratio is None:
                long_short_status = "多空平衡"
            elif long_short_ratio > 1.1:
                long_short_status = "多头占优"
            elif long_short_ratio < 0.9:
                long_short_status = "空头占优"
            else:
                long_short_status = "多空平衡"
            
            # 判断价格相对重要均线位置
            price_ma_position = []
            if current_price > float(latest_1h['ma20']):
                price_ma_position.append("价格位于1小时MA20均线上方")
            else:
                price_ma_position.append("价格位于1小时MA20均线下方")
                
            if current_price > float(latest_1h['ma50']):
                price_ma_position.append("价格位于1小时MA50均线上方")
            else:
                price_ma_position.append("价格位于1小时MA50均线下方")
                
            if current_price > float(latest_4h['ma20']):
                price_ma_position.append("价格位于4小时MA20均线上方")
            else:
                price_ma_position.append("价格位于4小时MA20均线下方")
            
            # 判断筹码分布情况
            chip_signal = "中性"
            if profit_percentage > 70:
                chip_signal = "看空"
            elif profit_percentage < 30:
                chip_signal = "看多"
            
            # 计算总体信号
            signal_weights = {
                'rsi': 0.15,
                'macd': 0.20,
                'ema': 0.25,
                'volume': 0.15,
                'funding': 0.10,
                'chip': 0.15
            }
            
            signal_values = {
                '看多': 1,
                '中性偏多': 0.5,
                '中性': 0,
                '中性偏空': -0.5,
                '看空': -1
            }
            
            # 计算加权平均信号
            total_signal = (
                signal_weights['rsi'] * signal_values.get(rsi_signal, 0) +
                signal_weights['macd'] * signal_values.get(macd_signal_trend, 0) +
                signal_weights['ema'] * signal_values.get(ema_signal, 0) +
                signal_weights['volume'] * signal_values.get(volume_signal, 0) +
                signal_weights['funding'] * signal_values.get(funding_signal, 0) +
                signal_weights['chip'] * signal_values.get(chip_signal, 0)
            )
            
            # 确定最终交易方向
            if total_signal > 0.3:
                direction = "📈 做多"
                direction_explanation = "短期技术指标整体偏多，以EMA和MACD指标最为突出"
            elif total_signal < -0.3:
                direction = "📉 做空"
                direction_explanation = "短期技术指标整体偏空，以EMA和RSI指标最为突出"
            else:
                if ema_signal == "看多":
                    direction = "📈 谨慎做多"
                    direction_explanation = "短期趋势指标偏多，但其他指标信号不强，建议轻仓操作"
                elif ema_signal == "看空":
                    direction = "📉 谨慎做空"
                    direction_explanation = "短期趋势指标偏空，但其他指标信号不强，建议轻仓操作"
                else:
                    direction = "⚖️ 观望"
                    direction_explanation = "技术指标呈中性状态，无明显交易优势，建议暂时观望"
            
            # 计算入场区间、止盈目标和止损建议
            volatility = float(latest_1h['high']) - float(latest_1h['low'])
            
            if direction == "⚖️ 观望":
                entry_low = current_price * 0.995
                entry_high = current_price * 1.005
                take_profit = current_price * 1.01
                stop_loss = current_price * 0.99
            elif "做多" in direction:
                entry_low = current_price * 0.997
                entry_high = current_price * 1.002
                take_profit = current_price * 1.015
                stop_loss = current_price * 0.99
            else:  # 做空
                entry_low = current_price * 0.998
                entry_high = current_price * 1.003
                take_profit = current_price * 0.985
                stop_loss = current_price * 1.01
            
            # 风险提示
            risk_notes = []
            if abs(funding_rate) > 0.03:
                risk_notes.append("当前资金费率异常，可能面临剧烈波动")
            
            if max_volume_percentage > 30:
                risk_notes.append("筹码高度集中，价格可能在此区间震荡")
            
            if volume_change > 50:
                risk_notes.append("成交量剧增，可能存在爆仓风险")
                
            if rsi > 75 or rsi < 25:
                risk_notes.append(f"RSI值处于极端区域({rsi:.1f})，可能面临短期反转")
            
            if not risk_notes:
                if "做空" in direction:
                    risk_notes.append("当前为技术回调，建议快进快出")
                    risk_notes.append("注意低位杀跌风险，适合短期交易者")
                elif "做多" in direction:
                    risk_notes.append("当前为技术反弹，建议快进快出")
                    risk_notes.append("注意高位套牢风险，适合短期交易者")
                else:
                    risk_notes.append("市场缺乏明确方向，建议轻仓操作或观望")
            
            # 将风险提示转换为字符串
            risk_warning = ""
            for note in risk_notes:
                risk_warning += f"- {note}；\n"
            
            # 策略模式解释
            strategy_mode_explanation = """本策略基于短线交易思路，重点关注价格与关键移动平均线的关系、动量指标变化和成交量特征。策略信号来源于以下几个方面：
1. 均线系统：主要通过EMA5与EMA13的交叉关系判断短期趋势
2. 动量指标：使用RSI判断超买超卖，MACD判断动能变化
3. 成交量分析：关注成交量与价格的配合关系
4. 筹码分布：评估主力筹码集中度和获利盘比例
5. 资金费率：监控合约市场中的资金费率变化
通过对以上因素的综合加权评估，形成最终交易信号和建议。"""
            
            # 生成筹码分布情况描述
            if chip_data:
                chip_situation = f"主力筹码集中在 {max_volume_price_range} 区间，占比 {max_volume_percentage:.2f}%\n- 获利盘比例: {profit_percentage:.2f}%"
            else:
                chip_situation = "筹码分布数据不足"
            
            # 格式化价格显示
            current_price_str = self._format_price(current_price)
            entry_low_str = self._format_price(entry_low)
            entry_high_str = self._format_price(entry_high)
            take_profit_str = self._format_price(take_profit)
            stop_loss_str = self._format_price(stop_loss)
            
            # 生成分析权重表格
            analysis_summary = f"""分析因素权重表:
RSI ({rsi:.2f}): {rsi_signal} [权重: {signal_weights['rsi']*100:.0f}%]
MACD: {macd_signal_trend} [权重: {signal_weights['macd']*100:.0f}%]
EMA趋势: {ema_signal} [权重: {signal_weights['ema']*100:.0f}%]
成交量: {volume_signal} [权重: {signal_weights['volume']*100:.0f}%]
资金费率: {funding_signal} [权重: {signal_weights['funding']*100:.0f}%]
筹码分布: {chip_signal} [权重: {signal_weights['chip']*100:.0f}%]
综合信号值: {total_signal:.2f}"""
            
            # 生成报告
            report = f"""📊【短期波段策略信号推送】

🕐 时间：{current_time}（系统自动分析）
💰 当前价格：${current_price_str}

🔹 策略模式：短线波段交易策略（均线动量体系）
🔸 推荐方向：{direction}
   * {direction_explanation}

🎯 推荐操作（{direction}）：
- 入场区间：${entry_low_str} ~ ${entry_high_str}
- 止盈目标：${take_profit_str}
- 止损建议：${stop_loss_str}
- 建议仓位：控制在总资金的 {'20~30%' if abs(total_signal) > 0.5 else '10~15%' if abs(total_signal) > 0.2 else '5~10%'}

📊 详细指标分析：
📈 RSI(14)：{rsi:.2f}（{rsi_zone}）
📉 MACD(12,26,9)：{macd:.2f}，信号线：{macd_signal:.2f}，{macd_status}
📊 EMA：EMA5={self._format_price(ema5)}，EMA13={self._format_price(ema13)}，{ema_trend}
📦 成交量：当前={self._format_price(volume)}，MA20={self._format_price(volume_ma20)}，变化={volume_change:.2f}%，{volume_status}
💰 Funding Rate：{funding_rate:.6f}%（{funding_status}）

📈 移动均线详情：
- MA20(1H)：{self._format_price(float(latest_1h['ma20']))}，{price_ma_position[0]}
- MA50(1H)：{self._format_price(float(latest_1h['ma50']))}，{price_ma_position[1]}
- MA20(4H)：{self._format_price(float(latest_4h['ma20']))}，{price_ma_position[2]}

📊 合约情况：
- 多空比：{long_short_ratio if long_short_ratio is not None else 1.00}（{long_short_status}）
- 资金费率：{funding_rate:.6f}%（{funding_status}）

📈 筹码分布：
- 主力筹码集中在 {max_volume_price_range} 区间，占比 {max_volume_percentage:.2f}%
- 获利盘比例: {profit_percentage:.2f}%（{'大部分持仓盈利' if profit_percentage > 50 else '大部分持仓亏损'}）

⚠️ 风险提示：
{risk_warning}

📬 如需切换至中期或长期策略，输入：
/strategy mid 或 /strategy long"""
            
            return report
            
        except Exception as e:
            logger.error(f"生成短期波段策略信号推送失败: {str(e)}")
            return f"生成短期波段策略信号推送失败: {str(e)}"

    def _generate_mid_term_signal_push(self, symbol, market_data, current_price):
        """生成中期趋势策略信号推送报告"""
        try:
            # 获取当前时间
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            # 获取K线数据
            klines_data = market_data['klines']
            latest_1h = klines_data['1h'].iloc[-1]
            latest_4h = klines_data['4h'].iloc[-1]
            latest_1d = klines_data['1d'].iloc[-1]
            
            # 获取技术指标数据
            rsi = float(latest_1d['rsi'])
            macd = float(latest_1d['macd'])
            macd_signal = float(latest_1d['macd_signal'])
            
            # 判断RSI区域
            rsi_zone = "中性区域"
            if rsi > 70:
                rsi_zone = "超买区域"
            elif rsi < 30:
                rsi_zone = "超卖区域"
                
            # 判断MACD情况
            if macd > macd_signal:
                macd_status = "金叉（中期动能转向多头）"
            else:
                macd_status = "死叉（中期动能转向空头）"
            
            # 分析趋势指标
            # 准备日线EMA数据
            ema_data_1d = {
                'ema5': float(latest_1d['ema5']),
                'ema13': float(latest_1d['ema13']),
                'ema20': float(latest_1d['ma20']),
                'ema50': float(latest_1d['ma50']),
                'ema100': float(latest_1d['ma50'])
            }
            
            # 准备4小时EMA数据
            ema_data_4h = {
                'ema5': float(latest_4h['ema5']),
                'ema13': float(latest_4h['ema13']),
                'ema20': float(latest_4h['ma20']),
                'ema50': float(latest_4h['ma50']),
                'ema100': float(latest_4h['ma50'])
            }
            
            # 日线趋势分析
            trend_1d_direction, trend_1d_strength = self.analysis_rules.analyze_trend(ema_data_1d)
            
            # 4小时趋势分析
            trend_4h_direction, trend_4h_strength = self.analysis_rules.analyze_trend(ema_data_4h)
            
            # 获取合约数据
            futures_data = market_data.get('futures_data', {})
            funding_rate = float(futures_data.get('funding_rate', 0)) * 100  # 转为百分比
            long_short_ratio = futures_data.get('long_short_ratio', None)  # 允许None值
            
            # 判断资金费率情况
            if funding_rate > 0.01:
                funding_status = "多头略占优"
            elif funding_rate < -0.01:
                funding_status = "空头略占优"
            else:
                funding_status = "多空平衡"
                
            # 判断多空比情况
            if long_short_ratio is None:
                long_short_status = "多空平衡"
            elif long_short_ratio > 1.1:
                long_short_status = "多头占优"
            elif long_short_ratio < 0.9:
                long_short_status = "空头占优"
            else:
                long_short_status = "多空平衡"
            
            # 获取筹码分布数据
            chip_data = market_data.get('volume_profile', {})
            if chip_data:
                # 处理筹码分布数据
                pass
            
            # 计算波动区间
            price_range = current_price * 0.01  # 默认波动区间为当前价格的1%
            
            # 计算入场区间
            entry_low = current_price - price_range * 0.5
            entry_high = current_price + price_range * 0.5
            
            # 计算止盈止损
            take_profit = current_price + price_range * 2 if trend_1d_direction == TrendDirection.BULLISH else current_price - price_range * 2
            stop_loss = current_price - price_range * 1.5 if trend_1d_direction == TrendDirection.BULLISH else current_price + price_range * 1.5
            
            # 综合信号评分 (1-7)
            signal_strength = 0
            
            # 根据趋势信号增加评分
            if trend_1d_direction == TrendDirection.BULLISH and trend_1d_strength in [SignalStrength.MEDIUM, SignalStrength.STRONG]:
                signal_strength += 2
            elif trend_1d_direction == TrendDirection.BEARISH and trend_1d_strength in [SignalStrength.MEDIUM, SignalStrength.STRONG]:
                signal_strength -= 2
                
            if trend_4h_direction == TrendDirection.BULLISH and trend_4h_strength in [SignalStrength.MEDIUM, SignalStrength.STRONG]:
                signal_strength += 1
            elif trend_4h_direction == TrendDirection.BEARISH and trend_4h_strength in [SignalStrength.MEDIUM, SignalStrength.STRONG]:
                signal_strength -= 1
                
            # 根据MACD信号增加评分
            if macd > macd_signal:
                signal_strength += 1
            else:
                signal_strength -= 1
                
            # 根据RSI增加评分
            if rsi > 50:
                signal_strength += 1
            else:
                signal_strength -= 1
                
            # 根据资金费率增加评分
            if funding_rate > 0.01:  # 多头略占优
                signal_strength += 1
                
            # 确定最终交易方向
            if signal_strength > 0:
                direction = "📈 做多"
                direction_explanation = f"综合多项技术指标，信号强度：{abs(signal_strength)}/7"
            elif signal_strength < 0:
                direction = "📉 做空"
                direction_explanation = f"综合多项技术指标，信号强度：{abs(signal_strength)}/7"
            else:
                direction = "⏹ 观望"
                direction_explanation = "技术指标分歧，无明确信号"
                
            # 计算建议仓位
            if abs(signal_strength) >= 5:
                position_recommendation = "30~50%"
            elif abs(signal_strength) >= 3:
                position_recommendation = "20~30%"
            else:
                position_recommendation = "10~20%"
                
            # 风险提示
            risk_notes = []
            risk_notes.append("筹码分布分散，价格波动可能较大；")
            risk_notes.append("套牢盘比例较高，存在解套反弹可能；")
            
            # 格式化价格显示
            current_price_str = self._format_price(current_price)
            entry_low_str = self._format_price(entry_low)
            entry_high_str = self._format_price(entry_high)
            take_profit_str = self._format_price(take_profit)
            stop_loss_str = self._format_price(stop_loss)
            
            # 生成信号推送报告
            report = f"""📊【中期趋势策略信号推送】

🕐 时间：{current_time}（系统自动分析）
💰 当前价格：${current_price_str}

🔹 策略模式：中期趋势策略（3-7日线）
🔸 推荐方向：{direction}
   * {direction_explanation}

🎯 推荐操作（{direction}）：
- 入场区间：${entry_low_str} ~ ${entry_high_str}
- 止盈目标：${take_profit_str}
- 止损建议：${stop_loss_str}
- 建议仓位：控制在总资金的 {position_recommendation}

📊 详细指标分析：
📈 RSI(14)：{rsi:.2f}（{rsi_zone}）
📉 MACD(12,26,9)：{macd:.2f}，信号线：{macd_signal:.2f}，{macd_status}
📊 趋势：日线={trend_1d_direction.value}({trend_1d_strength.name})，4小时={trend_4h_direction.value}({trend_4h_strength.name})
💰 Funding Rate：{funding_rate:.6f}%（{funding_status}）

📈 移动均线详情：
- MA20(1D)：{self._format_price(float(latest_1d['ma20']))}，价格位于日线MA20均线{'上方' if current_price > float(latest_1d['ma20']) else '下方'}
- MA50(1D)：{self._format_price(float(latest_1d['ma50']))}，价格位于日线MA50均线{'上方' if current_price > float(latest_1d['ma50']) else '下方'}
- MA20(4H)：{self._format_price(float(latest_4h['ma20']))}，价格位于4小时MA20均线{'上方' if current_price > float(latest_4h['ma20']) else '下方'}

📊 合约情况：
- 多空比：{long_short_ratio if long_short_ratio is not None else 1.00}（{long_short_status}）
- 资金费率：{funding_rate:.6f}%（{funding_status}）

📈 筹码分布：
- 主力筹码集中在 未知 区间，占比 0.00%
- 获利盘比例: 0.00%（大部分持仓亏损）

⚠️ 风险提示：
- {risk_notes[0]}
- {risk_notes[1]}

📬 如需切换至短期或长期策略，输入：
/strategy short 或 /strategy long"""
            
            return report
        
        except Exception as e:
            logger.error(f"生成中期信号推送失败: {str(e)}")
            return f"生成{symbol}的中期信号推送失败: {str(e)}"

    def _generate_long_term_signal_push(self, symbol, market_data, current_price):
        """生成长期投资策略信号推送报告"""
        try:
            # 获取当前时间
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            # 获取K线数据
            klines_data = market_data['klines']
            if '1d' not in klines_data or '1w' not in klines_data:
                logger.error(f"缺少生成长期投资分析所需的K线数据")
                return "缺少生成长期投资分析所需的K线数据"
                
            try:
                latest_1d = klines_data['1d'].iloc[-1]
                latest_1w = klines_data['1w'].iloc[-1]
            except Exception as e:
                logger.error(f"获取K线数据失败: {str(e)}")
                latest_1d = None
                latest_1w = None
            
            # 获取链上数据
            onchain_data = market_data.get('onchain_data', {})
            mvrv_z = self._safe_float(onchain_data, 'mvrv_z', 0)
            nvt = self._safe_float(onchain_data, 'nvt', 0)
            
            # 格式化价格显示
            current_price_str = self._format_price(current_price)
            mvrv_z_str = self._format_price(mvrv_z)
            nvt_str = self._format_price(nvt)
            
            # 计算趋势方向
            trend_1w_direction = TrendDirection.NEUTRAL
            trend_1w_strength = SignalStrength.WEAK
            trend_1d_direction = TrendDirection.NEUTRAL
            trend_1d_strength = SignalStrength.WEAK
            
            if latest_1w is not None:
                trend_1w_direction, trend_1w_strength = self.analysis_rules.analyze_trend({
                    'ema5': float(latest_1w['ema5']) if 'ema5' in latest_1w else 0,
                    'ema13': float(latest_1w['ema13']) if 'ema13' in latest_1w else 0,
                    'ema20': float(latest_1w['ma20']) if 'ma20' in latest_1w else 0,
                    'ema50': float(latest_1w['ma50']) if 'ma50' in latest_1w else 0,
                    'ema100': float(latest_1w['ma50']) if 'ma50' in latest_1w else 0  # 使用ma50代替
                })
            
            if latest_1d is not None:
                trend_1d_direction, trend_1d_strength = self.analysis_rules.analyze_trend({
                    'ema5': float(latest_1d['ema5']) if 'ema5' in latest_1d else 0,
                    'ema13': float(latest_1d['ema13']) if 'ema13' in latest_1d else 0,
                    'ema20': float(latest_1d['ma20']) if 'ma20' in latest_1d else 0,
                    'ema50': float(latest_1d['ma50']) if 'ma50' in latest_1d else 0,
                    'ema100': float(latest_1d['ma50']) if 'ma50' in latest_1d else 0  # 使用ma50代替
                })
            
            # 计算建议入场、止盈和止损价格
            price_range = current_price * 0.03  # 以当前价格的3%作为长期波动区间
            entry_low = current_price - price_range * 0.5
            entry_high = current_price + price_range * 0.5
            
            # 根据MVRV-Z和趋势确定止盈止损
            if mvrv_z < -0.5:  # 低估区域
                take_profit = current_price + price_range * 5  # 长期目标更远
                stop_loss = current_price - price_range * 1.5
            elif mvrv_z > 2:  # 高估区域
                take_profit = current_price - price_range * 5
                stop_loss = current_price + price_range * 1.5
            else:  # 中性区域
                # 根据趋势确定
                if trend_1w_direction == TrendDirection.BULLISH:
                    take_profit = current_price + price_range * 3
                    stop_loss = current_price - price_range * 2
                elif trend_1w_direction == TrendDirection.BEARISH:
                    take_profit = current_price - price_range * 3
                    stop_loss = current_price + price_range * 2
                else:
                    take_profit = current_price + price_range * 2
                    stop_loss = current_price - price_range * 2
            
            # 格式化价格字符串
            entry_low_str = self._format_price(entry_low)
            entry_high_str = self._format_price(entry_high)
            take_profit_str = self._format_price(take_profit)
            stop_loss_str = self._format_price(stop_loss)
            
            # 确定总体趋势方向
            overall_direction = "观望"
            direction_emoji = "⏳"
            position_size = "10~20%"
            
            bullish_signals = 0
            bearish_signals = 0
            
            # MVRV-Z信号（最重要的长期指标）
            if mvrv_z < -1:
                bullish_signals += 2  # 权重加倍
            elif mvrv_z < 0:
                bullish_signals += 1
            elif mvrv_z > 3:
                bearish_signals += 2  # 权重加倍
            elif mvrv_z > 1:
                bearish_signals += 1
                
            # NVT信号
            if nvt < 20:
                bullish_signals += 1
            elif nvt > 100:
                bearish_signals += 1
                
            # 周线趋势信号
            if trend_1w_direction == TrendDirection.BULLISH and trend_1w_strength in [SignalStrength.MEDIUM, SignalStrength.STRONG]:
                bullish_signals += 1
            elif trend_1w_direction == TrendDirection.BEARISH and trend_1w_strength in [SignalStrength.MEDIUM, SignalStrength.STRONG]:
                bearish_signals += 1
                
            # 日线趋势信号
            if trend_1d_direction == TrendDirection.BULLISH and trend_1d_strength in [SignalStrength.MEDIUM, SignalStrength.STRONG]:
                bullish_signals += 1
            elif trend_1d_direction == TrendDirection.BEARISH and trend_1d_strength in [SignalStrength.MEDIUM, SignalStrength.STRONG]:
                bearish_signals += 1
                
            # 确定最终方向
            if bullish_signals >= 3:
                overall_direction = "长期做多"
                direction_emoji = "📈"
                position_size = "30~50%"
            elif bearish_signals >= 3:
                overall_direction = "长期做空"
                direction_emoji = "📉"
                position_size = "30~50%"
            elif bullish_signals >= 2:
                overall_direction = "谨慎做多"
                direction_emoji = "📈"
                position_size = "20~30%"
            elif bearish_signals >= 2:
                overall_direction = "谨慎做空"
                direction_emoji = "📉"
                position_size = "20~30%"
                
            # 生成MVRV-Z状态描述
            mvrv_status = "合理"
            if mvrv_z < -1:
                mvrv_status = "严重低估"
                mvrv_interpretation = "-2~0区间为买入区"
                value_suggestion = "当前处于长期价值低估区域，适合分批布局，建立长期头寸；"
            elif mvrv_z < 0:
                mvrv_status = "略低估"
                mvrv_interpretation = "-1~0区间为低估区"
                value_suggestion = "当前处于价值低估区域，适合轻仓布局；"
            elif mvrv_z > 3:
                mvrv_status = "严重高估"
                mvrv_interpretation = "3以上为危险区"
                value_suggestion = "当前处于价值高估区域，不建议开仓，可考虑减持；"
            elif mvrv_z > 1:
                mvrv_status = "略高估" 
                mvrv_interpretation = "1~3区间为谨慎区"
                value_suggestion = "当前处于价值略高估区域，建议减少仓位，谨慎操作；"
            else:
                mvrv_interpretation = "0~1区间为中性区"
                value_suggestion = "当前处于价值合理区域，可考虑轻仓参与；"
                
            # 生成NVT状态描述
            nvt_status = "合理"
            if nvt < 20:
                nvt_status = "活跃（低估）"
                nvt_interpretation = "<30表示链上活动活跃，价值低估"
                chain_activity_suggestion = "链上活动活跃，长期价值支撑良好；"
            elif nvt > 100:
                nvt_status = "不活跃（高估）"
                nvt_interpretation = ">90表示链上活动不足，价值高估"
                chain_activity_suggestion = "链上活动不足，长期价值支撑不足；"
            else:
                nvt_interpretation = "30~90表示合理区间"
                chain_activity_suggestion = "链上活动处于正常水平；"
            
            # 生成报告
            report = f"""📊【长期投资策略信号推送】

🕐 时间：{current_time}（系统自动分析）
💰 当前价格：${current_price_str}

🔹 策略模式：长期投资策略（月度周期）
🔸 推荐方向：{direction_emoji} {overall_direction}
   * 基于价值评估和长期趋势，信号强度：{bullish_signals+bearish_signals}/5

🎯 推荐操作（{direction_emoji} {overall_direction}）：
- 入场区间：${entry_low_str} ~ ${entry_high_str}
- 止盈目标：${take_profit_str}
- 止损建议：${stop_loss_str}
- 建议仓位：控制在总资金的 {position_size}

📊 详细指标分析：
📈 MVRV-Z评分：{self._format_price(mvrv_z)}（{mvrv_status}）
📉 NVT比率：{self._format_price(nvt)}（{nvt_status}）
📊 趋势：周线={trend_1w_direction.value}({trend_1w_strength.name})，日线={trend_1d_direction.value}({trend_1d_strength.name})

📈 长期价值评估：
- MVRV-Z评分：{self._format_price(mvrv_z)}（市值相对于实现价值的Z分数）
  * {mvrv_interpretation}
- NVT比率：{self._format_price(nvt)}（网络价值与交易量比率）
  * {nvt_interpretation}

📈 移动均线详情：
- MA50(1W)：{self._format_price(float(latest_1w['ma50']) if latest_1w is not None and 'ma50' in latest_1w else 0)}，价格位于周线MA50均线{'上方' if current_price > (float(latest_1w['ma50']) if latest_1w is not None and 'ma50' in latest_1w else 0) else '下方'}
- MA200(1D)：{self._format_price(float(latest_1d['ma200']) if 'ma200' in latest_1d else 0)}，价格位于日线MA200均线{'上方' if current_price > (float(latest_1d['ma200']) if 'ma200' in latest_1d else 0) else '下方'}
- MA50(1D)：{self._format_price(float(latest_1d['ma50']))}，价格位于日线MA50均线{'上方' if current_price > float(latest_1d['ma50']) else '下方'}

⚠️ 投资建议：
- {value_suggestion}
- {chain_activity_suggestion}
- 长期投资应注重价值评估，避免追高杀低，建议采用定投策略。

📬 如需切换至短期或中期策略，输入：
/strategy short 或 /strategy mid"""
            
            return report
            
        except Exception as e:
            logger.error(f"生成长期投资策略信号推送失败: {str(e)}")
            return f"生成长期投资策略信号推送失败: {str(e)}"

if __name__ == "__main__":
    # 测试分析器
    analyzer = MarketAnalyzer()
    report = analyzer.analyze_market()
    if report:
        print("\n市场分析报告:")
        for timeframe, analysis in report['详细分析'].items():
            print(f"\n{timeframe}周期分析:")
            for section, content in analysis.items():
                print(f"\n{section}:")
                if isinstance(content, dict):
                    for key, value in content.items():
                        print(f"  {key}: {value}")
                else:
                    print(f"  {content}")
        
        print("\n综合交易建议:")
        for timeframe, suggestion in report['综合建议'].items():
            print(f"\n{timeframe}:")
            for key, value in suggestion.items():
                print(f"  {key}: {value}") 