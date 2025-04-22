import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class MarketAnalysis:
    def __init__(self, market_data):
        self.market_data = market_data

    def analyze_market(self, symbol):
        """分析市场数据"""
        try:
            logger.info(f"开始分析{symbol}的市场数据...")
            
            # 获取市场数据
            market_data = self.market_data.get_market_analysis()
            if not market_data:
                logger.error("获取市场数据失败")
                return "获取市场数据失败"
                
            # 整合分析结果
            analysis = []
            
            # 遍历所有时间周期
            for timeframe, data in market_data.items():
                try:
                    logger.info(f"分析{timeframe}周期数据...")
                    
                    # 检查数据是否有效
                    if not data.get('klines') is not None or data['klines'].empty:
                        logger.warning(f"{timeframe}周期数据无效")
                        continue
                        
                    # 分析价格趋势
                    price_analysis = self._analyze_price_trend(data['klines'])
                    if not price_analysis:
                        logger.warning(f"{timeframe}周期价格趋势分析失败")
                        continue
                        
                    # 分析成交量
                    volume_analysis = self._analyze_volume(data['klines'])
                    if not volume_analysis:
                        logger.warning(f"{timeframe}周期成交量分析失败")
                        continue
                        
                    # 分析合约数据
                    futures_analysis = self._analyze_futures_data(data['futures_data'])
                    if not futures_analysis:
                        logger.warning(f"{timeframe}周期合约数据分析失败")
                        continue
                        
                    # 分析筹码分布
                    chip_analysis = self._analyze_chip_distribution(data['volume_profile'])
                    if not chip_analysis:
                        logger.warning(f"{timeframe}周期筹码分布分析失败")
                        continue
                        
                    # 生成交易建议
                    trading_suggestions = self._generate_trading_suggestions(
                        price_analysis, volume_analysis, futures_analysis, chip_analysis
                    )
                    
                    # 添加时间周期分析结果
                    analysis.append(f"📊 {symbol} 市场分析报告 ({timeframe})")
                    analysis.append("\n📈 价格趋势分析:")
                    analysis.append(price_analysis)
                    analysis.append("\n💰 成交量分析:")
                    analysis.append(volume_analysis)
                    analysis.append("\n📊 合约数据分析:")
                    analysis.append(futures_analysis)
                    analysis.append("\n🎯 筹码分布分析:")
                    analysis.append(chip_analysis)
                    analysis.append("\n💡 交易建议:")
                    analysis.append(trading_suggestions)
                    analysis.append("\n" + "="*50 + "\n")
                    
                except Exception as e:
                    logger.error(f"分析{timeframe}周期数据失败: {str(e)}")
                    continue
            
            if not analysis:
                logger.error("所有时间周期的分析都失败了")
                return "分析市场数据失败"
                
            return "\n".join(analysis)
            
        except Exception as e:
            logger.error(f"分析市场数据失败: {str(e)}")
            return "分析市场数据失败"

    def analyze_multiple_timeframes(self, symbol):
        """分析多个时间周期的市场数据"""
        try:
            timeframes = ['1h', '4h', '1d', '3d', '1w']
            analysis_results = []
            
            for timeframe in timeframes:
                analysis = self.analyze_market(symbol, timeframe)
                if analysis:
                    analysis_results.append(analysis)
            
            if not analysis_results:
                return "所有时间周期的分析都失败了"
                
            return "\n\n" + "="*50 + "\n\n".join(analysis_results) + "\n" + "="*50
            
        except Exception as e:
            logger.error(f"多时间周期分析失败: {str(e)}")
            return "多时间周期分析失败"

    def _analyze_futures(self, futures_data):
        """分析合约数据"""
        try:
            if 'error' in futures_data:
                return futures_data['error']
                
            analysis = []
            
            # 分析持仓量
            if futures_data['open_interest'] > 0:
                analysis.append(f"• 合约持仓量: {futures_data['open_interest']:.2f}")
            else:
                analysis.append("• 合约持仓量: 数据不可用")
                
            # 分析资金费率
            if futures_data['funding_rate'] != 0:
                analysis.append(f"• 资金费率: {futures_data['funding_rate']*100:.4f}%")
                if futures_data['funding_rate'] > 0.01:
                    analysis.append("  - 资金费率较高，多头需支付较多费用")
                elif futures_data['funding_rate'] < -0.01:
                    analysis.append("  - 资金费率为负，空头需支付较多费用")
            else:
                analysis.append("• 资金费率: 数据不可用")
                
            # 分析多空比
            if futures_data['long_short_ratio'] != 1.0:
                analysis.append(f"• 多空比: {futures_data['long_short_ratio']:.2f}")
                if futures_data['long_short_ratio'] > 1.5:
                    analysis.append("  - 多头持仓明显高于空头")
                elif futures_data['long_short_ratio'] < 0.67:
                    analysis.append("  - 空头持仓明显高于多头")
            else:
                analysis.append("• 多空比: 数据不可用")
                
            return "\n".join(analysis)
            
        except Exception as e:
            logger.error(f"分析合约数据失败: {str(e)}")
            return "分析合约数据失败"

    def _analyze_price_trend(self, df):
        """分析价格趋势"""
        try:
            analysis = []
            
            # 获取最新数据
            current_price = df['close'].iloc[-1]
            rsi = df['rsi'].iloc[-1]
            macd = df['macd'].iloc[-1]
            macd_signal = df['macd_signal'].iloc[-1]
            ema5 = df['ema5'].iloc[-1]
            ema13 = df['ema13'].iloc[-1]
            bb_upper = df['bb_upper'].iloc[-1]
            bb_lower = df['bb_lower'].iloc[-1]
            
            # RSI分析
            if rsi < 30:
                analysis.append("• RSI < 30：超卖区域，有反弹可能")
            elif rsi > 70:
                analysis.append("• RSI > 70：超买区域，有回调风险")
            else:
                analysis.append("• RSI在正常区间：行情震荡")
                
            # MACD分析
            if macd > macd_signal:
                analysis.append("• MACD金叉：看涨信号")
            elif macd < macd_signal:
                analysis.append("• MACD死叉：看跌信号")
                
            # EMA分析
            if ema5 > ema13:
                analysis.append("• EMA5上穿EMA13：短期金叉，看涨")
            elif ema5 < ema13:
                analysis.append("• EMA5下穿EMA13：短期死叉，看跌")
                
            # 布林带分析
            if current_price < bb_lower:
                analysis.append("• 价格击穿布林带下轨：超跌反弹可能")
            elif current_price > bb_upper:
                analysis.append("• 价格击穿布林带上轨：警惕回调风险")
                
            return "\n".join(analysis)
            
        except Exception as e:
            logger.error(f"分析价格趋势失败: {str(e)}")
            return "分析价格趋势失败"
            
    def _analyze_volume(self, df):
        """分析成交量"""
        try:
            analysis = []
            
            # 获取最新数据
            current_volume = df['volume'].iloc[-1]
            avg_volume = df['volume'].mean()
            
            # 成交量分析
            if current_volume > avg_volume * 1.5:
                analysis.append("• 成交量显著放大：信号强度高")
            elif current_volume < avg_volume * 0.5:
                analysis.append("• 成交量萎缩：需谨慎对待")
            else:
                analysis.append("• 成交量正常：信号强度一般")
                
            return "\n".join(analysis)
            
        except Exception as e:
            logger.error(f"分析成交量失败: {str(e)}")
            return "分析成交量失败"
            
    def _analyze_futures_data(self, futures_data):
        """分析合约数据"""
        try:
            analysis = []
            
            # 检查数据是否有效
            if futures_data is None:
                analysis.append("• 合约数据获取失败")
                return "\n".join(analysis)
            
            # 获取合约数据
            funding_rate = futures_data.get('funding_rate', 0)
            
            # 资金费率分析
            if funding_rate > 0.01:
                analysis.append("• 资金费率过高：多头拥挤，回调概率大")
            elif funding_rate < -0.01:
                analysis.append("• 资金费率过低：空头拥挤，反弹概率大")
            else:
                analysis.append("• 资金费率正常：多空相对平衡")
                
            return "\n".join(analysis)
            
        except Exception as e:
            logger.error(f"分析合约数据失败: {str(e)}")
            return "分析合约数据失败"
            
    def _analyze_chip_distribution(self, volume_profile):
        """分析筹码分布"""
        try:
            analysis = []
            total_volume = sum(volume_profile.values())
            
            # 计算每个价格区间的筹码占比
            for price_range, volume in volume_profile.items():
                percentage = (volume / total_volume) * 100
                analysis.append(f"• 价格区间 {price_range}: {percentage:.2f}%")
                
            # 找出筹码密集区
            max_volume_range = max(volume_profile.items(), key=lambda x: x[1])[0]
            analysis.append(f"\n• 筹码密集区: {max_volume_range}")
            
            # 分析筹码分布特征
            if len(volume_profile) > 0:
                upper_half = sum(list(volume_profile.values())[len(volume_profile)//2:]) / total_volume
                if upper_half > 0.6:
                    analysis.append("  - 筹码主要分布在上方，存在获利盘压力")
                elif upper_half < 0.4:
                    analysis.append("  - 筹码主要分布在下方，存在支撑")
                else:
                    analysis.append("  - 筹码分布相对均匀")
                    
            return "\n".join(analysis)
            
        except Exception as e:
            logger.error(f"分析筹码分布失败: {str(e)}")
            return "分析筹码分布失败"

    def _generate_trading_suggestions(self, price_analysis, volume_analysis, futures_analysis, chip_analysis):
        """生成交易建议"""
        suggestions = []
        
        # 价格趋势建议
        if "看涨信号" in price_analysis and "成交量显著放大" in volume_analysis:
            suggestions.append("✅ 考虑做多")
        elif "看跌信号" in price_analysis and "成交量显著放大" in volume_analysis:
            suggestions.append("⚠️ 考虑做空")
        else:
            suggestions.append("🔄 建议观望，等待更明确的信号")
            
        # 成交量建议
        if "成交量显著放大" in volume_analysis:
            suggestions.append("📈 当前趋势可能持续")
        elif "成交量萎缩" in volume_analysis:
            suggestions.append("⚠️ 注意趋势可能反转")
            
        # 合约数据建议
        if "多头拥挤" in futures_analysis:
            suggestions.append("📊 注意回调风险")
        elif "空头拥挤" in futures_analysis:
            suggestions.append("📊 注意反弹可能")
            
        # 风险提示
        suggestions.append("\n⚠️ 风险提示：")
        suggestions.append("1. 以上分析仅供参考，不构成投资建议")
        suggestions.append("2. 短期波段交易风险较大，请控制仓位")
        suggestions.append("3. 建议设置止损止盈，严格执行交易计划")
        
        return "\n".join(suggestions) 