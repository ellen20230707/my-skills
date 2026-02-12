"""
技术指标计算模块

本模块实现各种股票技术指标的计算，包括：
- MACD（异同移动平均线）
- MA（移动平均线）
- 成交量比率
- RSI（相对强弱指标）
- KDJ（随机指标）
- 布林带（Bollinger Bands）

所有计算使用Pandas向量化操作，确保高效性能。

Author: Claude
Date: 2026-02-09
"""

import pandas as pd
import numpy as np
from typing import Tuple, Optional


def calculate_macd(
    df: pd.DataFrame,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9
) -> pd.DataFrame:
    """
    计算MACD指标

    MACD = 快速EMA - 慢速EMA
    信号线(DEA) = MACD的EMA
    MACD柱状图 = 2 * (MACD - 信号线)

    Args:
        df: 包含'close'列的DataFrame
        fast: 快速EMA周期，默认12
        slow: 慢速EMA周期，默认26
        signal: 信号线周期，默认9

    Returns:
        pd.DataFrame: 包含'macd_dif', 'macd_dea', 'macd_hist'三列的DataFrame
    """
    close = df['close']

    # 计算快速和慢速EMA
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()

    # DIF线（MACD线）
    dif = ema_fast - ema_slow

    # DEA线（信号线）
    dea = dif.ewm(span=signal, adjust=False).mean()

    # MACD柱状图
    macd = (dif - dea) * 2

    return pd.DataFrame({
        'macd_dif': dif,
        'macd_dea': dea,
        'macd_hist': macd
    }, index=df.index)


def calculate_ma(
    df: pd.DataFrame,
    period: int = 60
) -> pd.Series:
    """
    计算移动平均线

    Args:
        df: 包含'close'列的DataFrame
        period: 均线周期，默认60

    Returns:
        pd.Series: 移动平均线值
    """
    return df['close'].rolling(window=period).mean()


def calculate_volume_ratio(
    df: pd.DataFrame,
    recent: int = 3,
    baseline: int = 20
) -> pd.DataFrame:
    """
    计算成交量比率

    近期日均量 = 最近N天的平均成交量
    历史日均量 = 之前M天的平均成交量
    成交量比率 = 近期日均量 / 历史日均量

    Args:
        df: 包含'volume'列的DataFrame
        recent: 近期天数，默认3
        baseline: 基准天数，默认20

    Returns:
        pd.DataFrame: 包含'volume_recent', 'volume_baseline', 'volume_ratio'列
    """
    result = df.copy()

    # 近期日均成交量
    result['volume_recent'] = df['volume'].rolling(window=recent).mean()

    # 历史日均成交量（向前偏移，排除近期天数）
    result['volume_baseline'] = df['volume'].shift(recent).rolling(window=baseline).mean()

    # 成交量比率
    result['volume_ratio'] = result['volume_recent'] / result['volume_baseline']

    return result[['volume_recent', 'volume_baseline', 'volume_ratio']]


def calculate_rsi(
    df: pd.DataFrame,
    period: int = 14
) -> pd.Series:
    """
    计算RSI相对强弱指标

    RSI = 100 - (100 / (1 + RS))
    RS = 平均涨幅 / 平均跌幅

    Args:
        df: 包含'close'列的DataFrame
        period: RSI周期，默认14

    Returns:
        pd.Series: RSI值
    """
    # 计算价格变动
    delta = df['close'].diff()

    # 分离涨跌
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    # 计算平均涨跌幅
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()

    # 计算RS和RSI
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return rsi


def calculate_kdj(
    df: pd.DataFrame,
    n: int = 9,
    m1: int = 3,
    m2: int = 3
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    计算KDJ随机指标

    RSV = (收盘价 - 最低价) / (最高价 - 最低价) * 100
    K = RSV的移动平均
    D = K的移动平均
    J = 3K - 2D

    Args:
        df: 包含'close', 'high', 'low'列的DataFrame
        n: RSV周期，默认9
        m1: K值平滑参数，默认3
        m2: D值平滑参数，默认3

    Returns:
        Tuple[pd.Series, pd.Series, pd.Series]: K值, D值, J值
    """
    # 计算N日内的最低价和最高价
    low_list = df['low'].rolling(window=n).min()
    high_list = df['high'].rolling(window=n).max()

    # 计算RSV
    rsv = (df['close'] - low_list) / (high_list - low_list) * 100

    # 计算K值（RSV的移动平均，使用EWM模拟SMA）
    k = rsv.ewm(com=m1-1, adjust=False).mean()

    # 计算D值（K值的移动平均）
    d = k.ewm(com=m2-1, adjust=False).mean()

    # 计算J值
    j = 3 * k - 2 * d

    return k, d, j


def calculate_bollinger_bands(
    df: pd.DataFrame,
    period: int = 20,
    std_dev: float = 2.0
) -> pd.DataFrame:
    """
    计算布林带指标

    中轨 = N日均线
    上轨 = 中轨 + K * 标准差
    下轨 = 中轨 - K * 标准差
    带宽 = (上轨 - 下轨) / 中轨

    Args:
        df: 包含'close'列的DataFrame
        period: 布林带周期，默认20
        std_dev: 标准差倍数，默认2.0

    Returns:
        pd.DataFrame: 包含'boll_upper', 'boll_middle', 'boll_lower', 'boll_width'列
    """
    # 计算中轨（移动平均线）
    middle = df['close'].rolling(window=period).mean()

    # 计算标准差
    std = df['close'].rolling(window=period).std()

    # 计算上轨和下轨
    upper = middle + std_dev * std
    lower = middle - std_dev * std

    # 计算带宽
    width = (upper - lower) / middle

    return pd.DataFrame({
        'boll_upper': upper,
        'boll_middle': middle,
        'boll_lower': lower,
        'boll_width': width
    }, index=df.index)


def calculate_all_indicators(
    df: pd.DataFrame,
    config
) -> pd.DataFrame:
    """
    计算所有技术指标

    统一接口，一次性计算所有需要的技术指标并添加到DataFrame中。

    Args:
        df: 原始股票数据DataFrame，至少包含date, open, high, low, close, volume列
        config: 配置对象，包含各指标的参数

    Returns:
        pd.DataFrame: 添加了所有技术指标列的DataFrame
    """
    result = df.copy()

    # 确保数据按日期排序
    if 'date' in result.columns:
        result = result.sort_values('date').reset_index(drop=True)

    # 1. MACD指标
    macd_data = calculate_macd(
        result,
        fast=config.MACD_FAST,
        slow=config.MACD_SLOW,
        signal=config.MACD_SIGNAL
    )
    result = pd.concat([result, macd_data], axis=1)

    # 2. 移动平均线
    # 计算常用均线：5日、10日、20日、60日
    result['ma5'] = calculate_ma(result, period=5)
    result['ma10'] = calculate_ma(result, period=10)
    result['ma20'] = calculate_ma(result, period=20)

    # 尝试使用60日均线，如果数据不足则使用30日均线
    if len(result) >= config.MA_PERIOD:
        result['ma60'] = calculate_ma(result, period=config.MA_PERIOD)
        result['ma_period_used'] = config.MA_PERIOD
    elif len(result) >= config.MA_PERIOD_FALLBACK:
        result['ma60'] = calculate_ma(result, period=config.MA_PERIOD_FALLBACK)
        result['ma_period_used'] = config.MA_PERIOD_FALLBACK
    else:
        result['ma60'] = np.nan
        result['ma_period_used'] = 0

    # 3. 成交量比率
    volume_data = calculate_volume_ratio(
        result,
        recent=config.VOLUME_RECENT_DAYS,
        baseline=config.VOLUME_BASELINE_DAYS
    )
    result = pd.concat([result, volume_data], axis=1)

    # 4. RSI指标
    result['rsi'] = calculate_rsi(result, period=config.RSI_PERIOD)

    # 5. KDJ指标
    k, d, j = calculate_kdj(
        result,
        n=config.KDJ_PARAMS[0],
        m1=config.KDJ_PARAMS[1],
        m2=config.KDJ_PARAMS[2]
    )
    result['kdj_k'] = k
    result['kdj_d'] = d
    result['kdj_j'] = j

    # 6. 布林带指标
    boll_data = calculate_bollinger_bands(
        result,
        period=config.BOLL_PERIOD,
        std_dev=config.BOLL_STD
    )
    result = pd.concat([result, boll_data], axis=1)

    # 7. 计算MA60距离百分比
    result['ma60_distance'] = (result['high'] - result['ma60']) / result['ma60'] * 100

    # 8. 计算价格涨跌幅（用于量价配合判断）
    result['price_change_3d'] = (result['close'] - result['close'].shift(3)) / result['close'].shift(3) * 100

    return result


def check_data_quality(df: pd.DataFrame) -> Tuple[bool, str]:
    """
    检查数据质量

    Args:
        df: 股票数据DataFrame

    Returns:
        Tuple[bool, str]: (是否通过, 原因描述)
    """
    # 检查必要的列
    required_columns = ['date', 'open', 'high', 'low', 'close', 'volume', 'amount']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        return False, f"缺少必要列: {', '.join(missing_columns)}"

    # 检查数据量
    if len(df) < 34:  # MACD最少需要34个交易日
        return False, f"数据不足34天({len(df)}行)"

    # 检查是否有缺失值
    if df[required_columns].isnull().any().any():
        null_counts = df[required_columns].isnull().sum()
        null_cols = null_counts[null_counts > 0].to_dict()
        return False, f"存在缺失值: {null_cols}"

    # 检查价格数据有效性
    if (df['close'] <= 0).any():
        return False, "存在无效的收盘价(<=0)"

    if (df['volume'] < 0).any():
        return False, "存在无效的成交量(<0)"

    return True, "数据质量检查通过"


if __name__ == "__main__":
    # 简单测试
    from config import Config

    # 创建测试数据
    test_data = pd.DataFrame({
        'date': pd.date_range('2025-01-01', periods=100),
        'open': np.random.randn(100).cumsum() + 100,
        'high': np.random.randn(100).cumsum() + 105,
        'low': np.random.randn(100).cumsum() + 95,
        'close': np.random.randn(100).cumsum() + 100,
        'volume': np.random.randint(1000000, 10000000, 100),
        'amount': np.random.randint(10000000, 100000000, 100),
    })

    print("测试数据质量检查...")
    is_valid, message = check_data_quality(test_data)
    print(f"结果: {is_valid}, {message}")

    print("\n测试技术指标计算...")
    result = calculate_all_indicators(test_data, Config)
    print(f"原始列数: {len(test_data.columns)}")
    print(f"计算后列数: {len(result.columns)}")
    print(f"\n新增指标列:")
    new_columns = [col for col in result.columns if col not in test_data.columns]
    for col in new_columns:
        print(f"  - {col}")

    print("\n最后5行的MACD值:")
    print(result[['date', 'close', 'macd_dif', 'macd_dea', 'macd_hist']].tail())
