"""
信号检测模块

本模块实现股票上涨信号的检测逻辑，包括：
- MACD上涨趋势评分
- 核心特征检测（4个核心条件）
- 补充特征评分（RSI、KDJ等）
- 风险控制检查
- 综合评级

Author: Claude
Date: 2026-02-09
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any


def calculate_macd_score(df: pd.DataFrame, index: int, config) -> int:
    """
    计算MACD上涨趋势评分

    评分标准（满分100分）：
    - DIF > DEA（金叉状态）：+30分
    - DIF > 0 且 DEA > 0（零轴上方）：+20分
    - MACD柱状图 > 0：+15分
    - DIF连续5天上升：+20分
    - MACD柱连续3天递增：+15分

    Args:
        df: 包含MACD指标的DataFrame
        index: 当前分析的索引位置
        config: 配置对象

    Returns:
        int: MACD评分（0-100分）
    """
    score = 0
    weights = config.MACD_SCORE_WEIGHTS

    # 获取当前行数据
    row = df.iloc[index]

    # 条件1: DIF > DEA（金叉状态）
    if row['macd_dif'] > row['macd_dea']:
        score += weights['golden_cross']

    # 条件2: DIF > 0 且 DEA > 0（零轴上方）
    if row['macd_dif'] > 0 and row['macd_dea'] > 0:
        score += weights['above_zero']

    # 条件3: MACD柱状图 > 0
    if row['macd_hist'] > 0:
        score += weights['positive_hist']

    # 条件4: DIF连续5天上升
    if index >= 5:
        dif_values = df.iloc[index-4:index+1]['macd_dif'].values
        if all(dif_values[i] < dif_values[i+1] for i in range(len(dif_values)-1)):
            score += weights['dif_uptrend']

    # 条件5: MACD柱连续3天递增
    if index >= 3:
        hist_values = df.iloc[index-2:index+1]['macd_hist'].values
        if all(hist_values[i] < hist_values[i+1] for i in range(len(hist_values)-1)):
            score += weights['hist_increasing']

    return score


def check_volume_surge(df: pd.DataFrame, index: int, config) -> Tuple[bool, float]:
    """
    检查成交量放大条件

    Args:
        df: 包含成交量比率的DataFrame
        index: 当前分析的索引位置
        config: 配置对象

    Returns:
        Tuple[bool, float]: (是否满足条件, 成交量比率)
    """
    row = df.iloc[index]
    volume_ratio = row['volume_ratio']

    # 检查是否满足阈值
    is_surged = volume_ratio >= config.VOLUME_RATIO_THRESHOLD

    return is_surged, volume_ratio


def check_below_ma60(df: pd.DataFrame, index: int, config) -> Tuple[bool, float]:
    """
    检查最高价未高于60日均线条件

    Args:
        df: 包含MA60和high的DataFrame
        index: 当前分析的索引位置
        config: 配置对象

    Returns:
        Tuple[bool, float]: (是否满足条件, 距离百分比)
    """
    row = df.iloc[index]

    # 如果MA60为空，跳过
    if pd.isna(row['ma60']):
        return False, float('inf')

    # 计算距离百分比
    distance_pct = row['ma60_distance']

    # 检查是否满足条件（距离 <= 阈值）
    is_below = distance_pct <= config.MA_DISTANCE_THRESHOLD

    return is_below, distance_pct


def check_future_rise(df: pd.DataFrame, index: int, config) -> Tuple[bool, float]:
    """
    检查未来5日涨幅条件（仅用于回测）

    Args:
        df: 包含close和high的DataFrame
        index: 当前分析的索引位置
        config: 配置对象

    Returns:
        Tuple[bool, float]: (是否满足条件, 未来涨幅%)
    """
    # 检查是否有足够的未来数据
    if index + config.FUTURE_DAYS >= len(df):
        return False, 0.0

    current_close = df.iloc[index]['close']

    # 计算未来N日的最高价
    future_data = df.iloc[index+1:index+config.FUTURE_DAYS+1]
    future_high = future_data['high'].max()

    # 计算涨幅
    future_return = (future_high - current_close) / current_close * 100

    # 检查是否满足条件
    is_rise = future_return >= config.MIN_FUTURE_RETURN

    return is_rise, future_return


def calculate_enhanced_score(df: pd.DataFrame, index: int, config) -> Tuple[int, Dict[str, Any]]:
    """
    计算补充特征评分

    评分标准（满分60分）：
    - RSI在黄金区间：+10分
    - KDJ金叉信号：+15分
    - 布林带收窄：+10分
    - 价格形态良好：+15分
    - 量价齐升：+10分

    Args:
        df: 包含所有指标的DataFrame
        index: 当前分析的索引位置
        config: 配置对象

    Returns:
        Tuple[int, Dict]: (总评分, 详细信息字典)
    """
    score = 0
    details = {}
    weights = config.ENHANCED_SCORE_WEIGHTS

    row = df.iloc[index]

    # 特征1: RSI在黄金区间
    if not pd.isna(row['rsi']):
        rsi_value = row['rsi']
        if config.RSI_RANGE[0] < rsi_value < config.RSI_RANGE[1]:
            score += weights['rsi']
            details['rsi'] = {'value': rsi_value, 'status': '黄金区间'}
        else:
            details['rsi'] = {'value': rsi_value, 'status': '区间外'}

    # 特征2: KDJ金叉信号
    if index >= 1 and not pd.isna(row['kdj_k']) and not pd.isna(row['kdj_d']):
        k_curr = row['kdj_k']
        d_curr = row['kdj_d']
        j_curr = row['kdj_j']

        k_prev = df.iloc[index-1]['kdj_k']
        d_prev = df.iloc[index-1]['kdj_d']

        # 检查金叉：前一天K<=D，当天K>D，且J<80
        if k_prev <= d_prev and k_curr > d_curr and j_curr < config.KDJ_J_THRESHOLD:
            score += weights['kdj']
            details['kdj'] = {'status': '金叉信号', 'k': k_curr, 'd': d_curr, 'j': j_curr}
        else:
            details['kdj'] = {'status': '无信号', 'k': k_curr, 'd': d_curr}

    # 特征3: 布林带收窄
    if not pd.isna(row['boll_width']):
        boll_width = row['boll_width']
        if boll_width < config.BOLL_WIDTH_THRESHOLD:
            score += weights['boll']
            details['boll'] = {'width': boll_width, 'status': '收窄待突破'}
        else:
            details['boll'] = {'width': boll_width, 'status': '正常'}

    # 特征4: 价格形态识别
    pattern = detect_price_pattern(df, index)
    if pattern:
        score += weights['pattern']
        details['pattern'] = pattern
    else:
        details['pattern'] = '无明显形态'

    # 特征5: 量价配合检查
    if not pd.isna(row['price_change_3d']) and not pd.isna(row['volume_ratio']):
        price_change = row['price_change_3d']
        volume_ratio = row['volume_ratio']

        # 量价齐升：价格上涨且成交量放大
        if price_change > 0 and volume_ratio > 1.5:
            score += weights['volume_price']
            details['volume_price'] = '量价齐升'
        else:
            details['volume_price'] = '不配合'

    return score, details


def detect_price_pattern(df: pd.DataFrame, index: int) -> Optional[str]:
    """
    识别价格形态

    支持的形态：
    - 突破平台
    - V型反转
    - 回调企稳

    Args:
        df: DataFrame
        index: 当前索引

    Returns:
        Optional[str]: 形态名称，无形态则返回None
    """
    # 需要足够的历史数据
    if index < 20:
        return None

    row = df.iloc[index]

    # 形态1: 突破平台（20日内横盘突破）
    if index >= 20:
        recent_20 = df.iloc[index-19:index+1]
        high_20 = recent_20['high'].max()
        low_20 = recent_20['low'].min()
        platform_height = (high_20 - low_20) / low_20

        if platform_height < 0.10:  # 振幅小于10%
            if row['close'] > high_20 * 0.98:  # 接近或突破平台顶部
                return '突破平台'

    # 形态2: V型反转
    if index >= 10:
        recent_10 = df.iloc[index-9:index+1]['close'].values
        low_index = np.argmin(recent_10)

        if 3 <= low_index <= 7:  # 低点在中间位置
            left_drop = (recent_10[0] - recent_10[low_index]) / recent_10[0]
            right_rise = (recent_10[-1] - recent_10[low_index]) / recent_10[low_index]

            if left_drop > 0.05 and right_rise > 0.03:
                return 'V型反转'

    # 形态3: 回调企稳
    if index >= 60:
        recent_60 = df.iloc[index-59:index+1]
        high_60 = recent_60['high'].max()
        current_drawdown = (high_60 - row['close']) / high_60

        if 0.20 < current_drawdown < 0.50:
            # 检查近5日是否企稳
            if index >= 5:
                recent_5_gain = (row['close'] - df.iloc[index-5]['close']) / df.iloc[index-5]['close']
                if recent_5_gain > 0.02:
                    return '回调企稳'

    return None


def check_risk_control(df: pd.DataFrame, index: int, config) -> Tuple[bool, List[str]]:
    """
    风险控制检查

    排除以下高风险情况：
    1. 连续涨停 >= 3天
    2. 短期暴涨 > 30%
    3. 巨量滞涨
    4. 远离均线 > 30%

    Args:
        df: DataFrame
        index: 当前索引
        config: 配置对象

    Returns:
        Tuple[bool, List[str]]: (是否通过检查, 风险列表)
    """
    risks = []
    row = df.iloc[index]

    # 风险1: 检查连续涨停
    if index >= 5 and 'pctChg' in df.columns:
        recent_5 = df.iloc[index-4:index+1]['pctChg']
        limit_up_days = (recent_5 > 9.5).sum()

        if limit_up_days >= config.MAX_CONSECUTIVE_LIMIT_UP:
            risks.append(f'连续涨停{limit_up_days}天')

    # 风险2: 短期暴涨检查
    if index >= 5:
        price_5d_ago = df.iloc[index-5]['close']
        gain_5d = (row['close'] - price_5d_ago) / price_5d_ago * 100

        if gain_5d > config.MAX_SHORT_TERM_GAIN:
            risks.append(f'短期暴涨{gain_5d:.1f}%')

    # 风险3: 巨量滞涨检查
    if not pd.isna(row['volume_ratio']):
        if row['volume_ratio'] > config.VOLUME_SURGE_NO_GAIN:
            if not pd.isna(row['price_change_3d']):
                if row['price_change_3d'] < config.VOLUME_SURGE_MIN_GAIN:
                    risks.append('巨量滞涨')

    # 风险4: 远离均线检查
    if not pd.isna(row['ma20']):
        distance_ma20 = (row['close'] - row['ma20']) / row['ma20'] * 100
        if distance_ma20 > config.MAX_MA20_DEVIATION:
            risks.append(f'远离20日均线{distance_ma20:.1f}%')

    # 通过检查：无风险
    return len(risks) == 0, risks


def get_rating(enhanced_score: int, config) -> str:
    """
    根据补充特征评分获取评级

    Args:
        enhanced_score: 补充特征评分
        config: 配置对象

    Returns:
        str: 评级（A级/B级/C级）
    """
    thresholds = config.RATING_THRESHOLDS

    if enhanced_score >= thresholds['A']:
        return 'A级'
    elif enhanced_score >= thresholds['B']:
        return 'B级'
    else:
        return 'C级'


def detect_uptrend_signals(
    df: pd.DataFrame,
    config,
    enable_future_validation: bool = True
) -> List[Dict[str, Any]]:
    """
    检测上涨信号

    遍历DataFrame的每一行，检测是否满足上涨趋势的特征条件。

    Args:
        df: 包含所有技术指标的DataFrame
        config: 配置对象
        enable_future_validation: 是否启用未来涨幅验证（回测模式）

    Returns:
        List[Dict]: 信号列表，每个信号包含日期、价格、指标值、评级等信息
    """
    signals = []

    # 确定分析范围
    # 需要至少60天历史数据（MA60）
    start_index = 60
    # 如果启用未来验证，需要留出未来N天
    end_offset = config.FUTURE_DAYS if enable_future_validation else 0
    end_index = len(df) - end_offset

    if end_index <= start_index:
        return signals  # 数据不足，返回空列表

    # 遍历每个交易日
    for i in range(start_index, end_index):
        row = df.iloc[i]

        # 特征1: MACD上涨趋势评分
        macd_score = calculate_macd_score(df, i, config)

        # 特征2: 成交量放大
        volume_surged, volume_ratio = check_volume_surge(df, i, config)

        # 特征3: 最高价未高于60日均线
        below_ma60, ma60_distance = check_below_ma60(df, i, config)

        # 特征4: 未来涨幅验证（仅回测模式）
        if enable_future_validation:
            future_rise, future_return = check_future_rise(df, i, config)
        else:
            future_rise, future_return = True, 0.0  # 实盘模式不验证

        # 核心条件汇总
        conditions = {
            'macd_uptrend': macd_score >= config.MACD_SCORE_THRESHOLD,
            'volume_surge': volume_surged,
            'below_ma60': below_ma60,
            'future_rise': future_rise
        }

        # 计算满足的条件数
        pass_count = sum(conditions.values())

        # 根据筛选模式判断是否满足条件
        min_conditions = config.get_min_conditions()

        # 宽松模式额外要求：MACD必须满足
        if config.FILTER_MODE == 'loose':
            if not conditions['macd_uptrend']:
                continue

        # 检查是否满足最少条件数
        if pass_count < min_conditions:
            continue

        # 补充特征评分
        enhanced_score, enhanced_details = calculate_enhanced_score(df, i, config)

        # 风险控制检查
        risk_passed, risks = check_risk_control(df, i, config)

        # 如果存在风险，跳过此信号
        if not risk_passed:
            continue

        # 获取评级
        rating = get_rating(enhanced_score, config)

        # 构造信号字典
        signal = {
            'date': row['date'],
            'close': row['close'],
            'macd_score': macd_score,
            'volume_ratio': volume_ratio,
            'ma60_distance': ma60_distance,
            'future_return': future_return,
            'conditions': conditions,
            'pass_count': pass_count,
            'enhanced_score': enhanced_score,
            'enhanced_details': enhanced_details,
            'rating': rating,
            'risks': risks
        }

        signals.append(signal)

    return signals


if __name__ == "__main__":
    # 简单测试
    from config import Config
    from technical_indicators import calculate_all_indicators

    # 创建测试数据
    np.random.seed(42)
    test_data = pd.DataFrame({
        'date': pd.date_range('2025-01-01', periods=100),
        'open': np.random.randn(100).cumsum() + 100,
        'high': np.random.randn(100).cumsum() + 105,
        'low': np.random.randn(100).cumsum() + 95,
        'close': np.random.randn(100).cumsum() + 100,
        'volume': np.abs(np.random.randn(100) * 1000000 + 5000000),
        'amount': np.abs(np.random.randn(100) * 100000000 + 50000000),
        'pctChg': np.random.randn(100) * 3,
    })

    print("计算技术指标...")
    test_data = calculate_all_indicators(test_data, Config)

    print("检测上涨信号...")
    signals = detect_uptrend_signals(test_data, Config, enable_future_validation=True)

    print(f"\n共检测到 {len(signals)} 个信号")
    if signals:
        print("\n前3个信号:")
        for i, signal in enumerate(signals[:3], 1):
            print(f"\n信号{i}:")
            print(f"  日期: {signal['date']}")
            print(f"  收盘价: {signal['close']:.2f}")
            print(f"  MACD评分: {signal['macd_score']}")
            print(f"  成交量比率: {signal['volume_ratio']:.2f}")
            print(f"  评级: {signal['rating']}")
