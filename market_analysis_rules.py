from enum import Enum
from typing import Dict, List, Tuple

class SignalStrength(Enum):
    STRONG = 5
    MEDIUM = 3
    WEAK = 1

class TrendDirection(Enum):
    BULLISH = "看涨"
    BEARISH = "看跌"
    NEUTRAL = "震荡"

class IndicatorPriority(Enum):
    TREND = 1  # 趋势指标（最高优先级）
    MOMENTUM = 2  # 动量指标
    VOLUME = 3  # 成交量指标
    SUPPORT_RESISTANCE = 4  # 支撑阻力指标

class TechnicalAnalysisRules:
    # 趋势指标规则
    @staticmethod
    def analyze_trend(ema_data: Dict) -> Tuple[TrendDirection, SignalStrength]:
        """
        分析趋势指标
        :param ema_data: 包含EMA数据的字典
        :return: (趋势方向, 信号强度)
        """
        # 检查EMA多头排列
        if (ema_data['ema5'] > ema_data['ema13'] > ema_data['ema20'] and
            ema_data['ema13'] > ema_data['ema50'] > ema_data['ema100']):
            return TrendDirection.BULLISH, SignalStrength.STRONG
        
        # 检查EMA空头排列
        if (ema_data['ema5'] < ema_data['ema13'] < ema_data['ema20'] and
            ema_data['ema13'] < ema_data['ema50'] < ema_data['ema100']):
            return TrendDirection.BEARISH, SignalStrength.STRONG
        
        # 检查短期趋势
        if ema_data['ema5'] > ema_data['ema13']:
            return TrendDirection.BULLISH, SignalStrength.MEDIUM
        elif ema_data['ema5'] < ema_data['ema13']:
            return TrendDirection.BEARISH, SignalStrength.MEDIUM
        
        return TrendDirection.NEUTRAL, SignalStrength.WEAK

    # 动量指标规则
    @staticmethod
    def analyze_momentum(rsi: float, macd: float, macd_signal: float) -> Tuple[TrendDirection, SignalStrength]:
        """
        分析动量指标
        :param rsi: RSI值
        :param macd: MACD值
        :param macd_signal: MACD信号线值
        :return: (趋势方向, 信号强度)
        """
        signals = []
        
        # RSI分析
        if rsi < 30:
            signals.append((TrendDirection.BULLISH, SignalStrength.STRONG))
        elif rsi > 70:
            signals.append((TrendDirection.BEARISH, SignalStrength.STRONG))
        elif 30 <= rsi <= 70:
            signals.append((TrendDirection.NEUTRAL, SignalStrength.WEAK))
            
        # MACD分析
        if macd > macd_signal:
            signals.append((TrendDirection.BULLISH, SignalStrength.MEDIUM))
        elif macd < macd_signal:
            signals.append((TrendDirection.BEARISH, SignalStrength.MEDIUM))
        else:
            signals.append((TrendDirection.NEUTRAL, SignalStrength.WEAK))
            
        # 综合判断
        if all(s[0] == TrendDirection.BULLISH for s in signals):
            return TrendDirection.BULLISH, SignalStrength.STRONG
        elif all(s[0] == TrendDirection.BEARISH for s in signals):
            return TrendDirection.BEARISH, SignalStrength.STRONG
        elif any(s[0] == TrendDirection.BULLISH for s in signals):
            return TrendDirection.BULLISH, SignalStrength.MEDIUM
        elif any(s[0] == TrendDirection.BEARISH for s in signals):
            return TrendDirection.BEARISH, SignalStrength.MEDIUM
            
        return TrendDirection.NEUTRAL, SignalStrength.WEAK

    # 成交量指标规则
    @staticmethod
    def analyze_volume(current_volume: float, avg_volume: float, price_change: float) -> Tuple[TrendDirection, SignalStrength]:
        """
        分析成交量指标
        :param current_volume: 当前成交量
        :param avg_volume: 平均成交量
        :param price_change: 价格变化
        :return: (趋势方向, 信号强度)
        """
        volume_ratio = current_volume / avg_volume
        
        # 放量上涨
        if volume_ratio > 1.5 and price_change > 0:
            return TrendDirection.BULLISH, SignalStrength.STRONG
            
        # 放量下跌
        if volume_ratio > 1.5 and price_change < 0:
            return TrendDirection.BEARISH, SignalStrength.STRONG
            
        # 缩量上涨
        if volume_ratio < 0.8 and price_change > 0:
            return TrendDirection.BULLISH, SignalStrength.WEAK
            
        # 缩量下跌
        if volume_ratio < 0.8 and price_change < 0:
            return TrendDirection.BEARISH, SignalStrength.WEAK
            
        return TrendDirection.NEUTRAL, SignalStrength.WEAK

    # 支撑阻力指标规则
    @staticmethod
    def analyze_support_resistance(
        current_price: float,
        support_levels: List[float],
        resistance_levels: List[float],
        volume: float,
        avg_volume: float
    ) -> Tuple[TrendDirection, SignalStrength]:
        """
        分析支撑阻力指标
        :param current_price: 当前价格
        :param support_levels: 支撑位列表
        :param resistance_levels: 阻力位列表
        :param volume: 当前成交量
        :param avg_volume: 平均成交量
        :return: (趋势方向, 信号强度)
        """
        # 检查是否突破阻力位
        for resistance in resistance_levels:
            if current_price > resistance and volume > avg_volume * 1.5:
                return TrendDirection.BULLISH, SignalStrength.STRONG
                
        # 检查是否跌破支撑位
        for support in support_levels:
            if current_price < support and volume > avg_volume * 1.5:
                return TrendDirection.BEARISH, SignalStrength.STRONG
                
        # 检查是否在支撑位附近
        for support in support_levels:
            if abs(current_price - support) / support < 0.01:
                return TrendDirection.BULLISH, SignalStrength.MEDIUM
                
        # 检查是否在阻力位附近
        for resistance in resistance_levels:
            if abs(current_price - resistance) / resistance < 0.01:
                return TrendDirection.BEARISH, SignalStrength.MEDIUM
                
        return TrendDirection.NEUTRAL, SignalStrength.WEAK

    @staticmethod
    def generate_final_signal(
        trend_signal: Tuple[TrendDirection, SignalStrength],
        momentum_signal: Tuple[TrendDirection, SignalStrength],
        volume_signal: Tuple[TrendDirection, SignalStrength],
        support_resistance_signal: Tuple[TrendDirection, SignalStrength]
    ) -> Tuple[TrendDirection, SignalStrength]:
        """
        生成最终信号
        :param trend_signal: 趋势信号
        :param momentum_signal: 动量信号
        :param volume_signal: 成交量信号
        :param support_resistance_signal: 支撑阻力信号
        :return: (最终趋势方向, 最终信号强度)
        """
        # 收集所有信号
        signals = [
            (trend_signal, IndicatorPriority.TREND),
            (momentum_signal, IndicatorPriority.MOMENTUM),
            (volume_signal, IndicatorPriority.VOLUME),
            (support_resistance_signal, IndicatorPriority.SUPPORT_RESISTANCE)
        ]
        
        # 按优先级排序
        signals.sort(key=lambda x: x[1].value)
        
        # 计算加权信号
        total_strength = 0
        bullish_count = 0
        bearish_count = 0
        
        for (direction, strength), priority in signals:
            weight = 1 / priority.value
            total_strength += strength.value * weight
            
            if direction == TrendDirection.BULLISH:
                bullish_count += 1
            elif direction == TrendDirection.BEARISH:
                bearish_count += 1
                
        # 确定最终方向
        if bullish_count > bearish_count:
            final_direction = TrendDirection.BULLISH
        elif bearish_count > bullish_count:
            final_direction = TrendDirection.BEARISH
        else:
            final_direction = TrendDirection.NEUTRAL
            
        # 确定最终强度
        if total_strength >= 4:
            final_strength = SignalStrength.STRONG
        elif total_strength >= 2:
            final_strength = SignalStrength.MEDIUM
        else:
            final_strength = SignalStrength.WEAK
            
        return final_direction, final_strength 