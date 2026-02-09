"""
A股上涨趋势分析器

主程序入口，用于批量分析全市场A股股票，识别具有上涨趋势特征的股票。

功能：
1. 批量读取股票CSV文件
2. 计算技术指标
3. 检测上涨信号
4. 生成分析报告

使用方法:
    python stock_trend_analyzer.py

Author: Claude
Date: 2026-02-09
"""

import os
import glob
import logging
import json
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Tuple

from config import Config
from technical_indicators import calculate_all_indicators, check_data_quality
from signal_detector import detect_uptrend_signals


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(Config.OUTPUT_DIR, 'analysis.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def extract_stock_info(file_path: str) -> Tuple[str, str]:
    """
    从文件名提取股票代码和名称

    文件名格式: sh.600000_浦发银行_近10年日线.csv

    Args:
        file_path: CSV文件路径

    Returns:
        Tuple[str, str]: (股票代码, 股票名称)
    """
    filename = os.path.basename(file_path)
    # 移除扩展名
    name_part = filename.replace('.csv', '')

    # 分割代码和名称
    parts = name_part.split('_')
    if len(parts) >= 2:
        stock_code = parts[0]
        stock_name = parts[1]
    else:
        stock_code = parts[0]
        stock_name = "未知"

    return stock_code, stock_name


def pre_filter(df: pd.DataFrame, config: Config) -> Tuple[bool, str]:
    """
    数据质量预筛选

    快速过滤不符合基本条件的股票，减少计算量。

    筛选条件：
    1. 数据量 >= MIN_DATA_ROWS
    2. 近期无停牌（连续3天成交量=0）
    3. 价格区间检查
    4. 流动性检查（日均成交额）

    Args:
        df: 股票DataFrame
        config: 配置对象

    Returns:
        Tuple[bool, str]: (是否通过, 原因)
    """
    # 1. 数据量检查
    if len(df) < config.MIN_DATA_ROWS:
        return False, f"数据不足{config.MIN_DATA_ROWS}天"

    # 2. 停牌检查（最近3天成交量）
    if len(df) >= 3:
        recent_volumes = df.tail(3)['volume']
        if (recent_volumes == 0).sum() >= 2:
            return False, "近期停牌"

    # 3. 价格区间检查
    latest_price = df.iloc[-1]['close']
    if latest_price < config.PRICE_RANGE[0] or latest_price > config.PRICE_RANGE[1]:
        return False, f"价格({latest_price:.2f})超出范围"

    # 4. 流动性检查
    if len(df) >= 10:
        avg_amount = df.tail(10)['amount'].mean()
        if avg_amount < config.MIN_DAILY_AMOUNT:
            return False, "流动性不足"

    return True, "通过预筛选"


def analyze_single_stock(
    file_path: str,
    config: Config,
    enable_future_validation: bool = True
) -> Dict[str, Any]:
    """
    分析单只股票

    Args:
        file_path: CSV文件路径
        config: 配置对象
        enable_future_validation: 是否启用未来涨幅验证

    Returns:
        Dict: 分析结果，包含股票信息和信号列表
    """
    try:
        # 提取股票信息
        stock_code, stock_name = extract_stock_info(file_path)

        # 读取数据
        df = pd.read_csv(file_path)

        # 数据质量检查
        is_valid, message = check_data_quality(df)
        if not is_valid:
            logger.warning(f"{stock_code} {stock_name}: {message}")
            return None

        # 预筛选
        passed, reason = pre_filter(df, config)
        if not passed:
            logger.debug(f"{stock_code} {stock_name}: {reason}")
            return None

        # 计算技术指标
        df = calculate_all_indicators(df, config)

        # 检测上涨信号
        signals = detect_uptrend_signals(df, config, enable_future_validation)

        if not signals:
            return None

        # 返回结果
        return {
            'stock_code': stock_code,
            'stock_name': stock_name,
            'signal_count': len(signals),
            'signals': signals
        }

    except Exception as e:
        logger.error(f"{file_path}: 处理失败 - {str(e)}")
        return None


def analyze_all_stocks(
    data_dir: str = None,
    output_dir: str = None,
    config: Config = None,
    enable_future_validation: bool = True,
    limit: int = None
) -> Dict[str, Any]:
    """
    批量分析所有股票

    Args:
        data_dir: 数据目录，默认使用Config.DATA_DIR
        output_dir: 输出目录，默认使用Config.OUTPUT_DIR
        config: 配置对象，默认使用Config类
        enable_future_validation: 是否启用未来涨幅验证（回测模式）
        limit: 限制处理的股票数量（用于测试），None表示全部处理

    Returns:
        Dict: 分析结果汇总
    """
    # 使用默认配置
    if config is None:
        config = Config

    if data_dir is None:
        data_dir = config.DATA_DIR

    if output_dir is None:
        output_dir = config.OUTPUT_DIR

    # 验证配置
    try:
        config.validate()
    except ValueError as e:
        logger.error(f"配置验证失败: {e}")
        return None

    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    # 获取所有CSV文件
    csv_pattern = os.path.join(data_dir, "*.csv")
    csv_files = glob.glob(csv_pattern)

    if not csv_files:
        logger.error(f"未找到CSV文件: {csv_pattern}")
        return None

    # 如果设置了limit，只处理前N个文件
    if limit:
        csv_files = csv_files[:limit]

    logger.info(f"=" * 60)
    logger.info(f"A股上涨趋势分析工具")
    logger.info(f"=" * 60)
    logger.info(f"数据目录: {data_dir}")
    logger.info(f"输出目录: {output_dir}")
    logger.info(f"筛选模式: {config.FILTER_MODE} - {config.get_filter_description()}")
    logger.info(f"回测模式: {'开启' if enable_future_validation else '关闭'}")
    logger.info(f"待分析股票数: {len(csv_files)}")
    logger.info(f"=" * 60)

    # 存储所有结果
    all_signals = []
    stock_results = []
    processed_count = 0
    signal_count = 0
    fail_count = 0

    # 遍历处理每只股票
    for i, file_path in enumerate(csv_files, 1):
        try:
            result = analyze_single_stock(file_path, config, enable_future_validation)

            if result:
                # 有信号的股票
                stock_results.append({
                    'stock_code': result['stock_code'],
                    'stock_name': result['stock_name'],
                    'signal_count': result['signal_count']
                })

                # 展开所有信号
                for signal in result['signals']:
                    signal_data = {
                        'stock_code': result['stock_code'],
                        'stock_name': result['stock_name'],
                        **signal
                    }
                    all_signals.append(signal_data)
                    signal_count += 1

                processed_count += 1

            # 进度显示
            if i % config.PROGRESS_INTERVAL == 0:
                logger.info(f"进度: {i}/{len(csv_files)} | "
                           f"有信号: {processed_count} | "
                           f"信号总数: {signal_count}")

        except Exception as e:
            logger.error(f"{file_path}: {str(e)}")
            fail_count += 1

    logger.info(f"=" * 60)
    logger.info(f"分析完成!")
    logger.info(f"总股票数: {len(csv_files)}")
    logger.info(f"有信号股票: {processed_count} ({processed_count/len(csv_files)*100:.1f}%)")
    logger.info(f"信号总数: {signal_count}")
    logger.info(f"失败数: {fail_count}")
    logger.info(f"=" * 60)

    # 保存结果
    if all_signals:
        output_csv, output_json = save_results(all_signals, stock_results, output_dir, config, enable_future_validation)
        logger.info(f"结果已保存:")
        logger.info(f"  CSV: {output_csv}")
        logger.info(f"  JSON: {output_json}")
    else:
        logger.warning("未发现任何信号")

    # 返回汇总结果
    return {
        'total_stocks': len(csv_files),
        'stocks_with_signals': processed_count,
        'total_signals': signal_count,
        'fail_count': fail_count,
        'output_dir': output_dir
    }


def save_results(
    all_signals: List[Dict],
    stock_results: List[Dict],
    output_dir: str,
    config: Config,
    enable_future_validation: bool
) -> Tuple[str, str]:
    """
    保存分析结果

    Args:
        all_signals: 所有信号列表
        stock_results: 股票汇总列表
        output_dir: 输出目录
        config: 配置对象
        enable_future_validation: 是否启用未来验证

    Returns:
        Tuple[str, str]: (CSV路径, JSON路径)
    """
    timestamp = datetime.now().strftime(config.DATE_FORMAT)

    # 1. 保存CSV详细结果
    csv_filename = f"trend_signals_{timestamp}.csv"
    csv_path = os.path.join(output_dir, csv_filename)

    # 构造DataFrame
    csv_data = []
    for signal in all_signals:
        row = {
            '股票代码': signal['stock_code'],
            '股票名称': signal['stock_name'],
            '信号日期': signal['date'],
            '收盘价': round(signal['close'], 2),
            'MACD评分': signal['macd_score'],
            '成交量比率': round(signal['volume_ratio'], 2),
            'MA60距离%': round(signal['ma60_distance'], 2),
            '评级': signal['rating'],
            '补充特征分': signal['enhanced_score'],
        }

        # 核心特征满足情况
        row['MACD满足'] = signal['conditions']['macd_uptrend']
        row['成交量满足'] = signal['conditions']['volume_surge']
        row['MA60满足'] = signal['conditions']['below_ma60']

        # 如果是回测模式，添加未来涨幅
        if enable_future_validation:
            row['未来5日涨幅%'] = round(signal['future_return'], 2)
            row['未来涨幅满足'] = signal['conditions']['future_rise']

        csv_data.append(row)

    df_csv = pd.DataFrame(csv_data)
    df_csv.to_csv(csv_path, index=False, encoding=config.CSV_ENCODING)

    # 2. 保存JSON统计报告
    json_filename = f"analysis_report_{timestamp}.json"
    json_path = os.path.join(output_dir, json_filename)

    # 统计信息
    df_signals = pd.DataFrame(all_signals)

    # 按评级统计
    rating_stats = df_csv['评级'].value_counts().to_dict()

    # 计算性能指标（仅回测模式）
    performance_stats = {}
    if enable_future_validation:
        performance_stats = {
            'avg_future_return': round(df_signals['future_return'].mean(), 2),
            'median_future_return': round(df_signals['future_return'].median(), 2),
            'win_rate': round((df_signals['future_return'] >= config.MIN_FUTURE_RETURN).mean() * 100, 2),
            'max_return': round(df_signals['future_return'].max(), 2),
            'min_return': round(df_signals['future_return'].min(), 2),
        }

    # Top信号股票
    stock_df = pd.DataFrame(stock_results).sort_values('signal_count', ascending=False)
    top_stocks = stock_df.head(20).to_dict('records')

    # 构造JSON报告
    report = {
        'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'mode': 'backtest' if enable_future_validation else 'realtime',
        'config': {
            'filter_mode': config.FILTER_MODE,
            'volume_ratio_threshold': config.VOLUME_RATIO_THRESHOLD,
            'macd_score_threshold': config.MACD_SCORE_THRESHOLD,
            'min_future_return': config.MIN_FUTURE_RETURN if enable_future_validation else None,
        },
        'summary': {
            'total_stocks': len(stock_results),
            'total_signals': len(all_signals),
            'avg_signals_per_stock': round(len(all_signals) / len(stock_results), 2) if stock_results else 0,
        },
        'rating_distribution': rating_stats,
        'performance_stats': performance_stats,
        'top_stocks': top_stocks,
        'indicator_stats': {
            'avg_macd_score': round(df_signals['macd_score'].mean(), 2),
            'avg_volume_ratio': round(df_signals['volume_ratio'].mean(), 2),
            'avg_enhanced_score': round(df_signals['enhanced_score'].mean(), 2),
        }
    }

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    return csv_path, json_path


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='A股上涨趋势分析工具')
    parser.add_argument('--data-dir', help='数据目录路径')
    parser.add_argument('--output-dir', help='输出目录路径')
    parser.add_argument('--no-future', action='store_true', help='关闭未来验证（实盘模式）')
    parser.add_argument('--limit', type=int, help='限制处理的股票数量（测试用）')
    parser.add_argument('--mode', choices=['strict', 'standard', 'loose'], help='筛选模式')

    args = parser.parse_args()

    # 更新配置
    if args.mode:
        Config.FILTER_MODE = args.mode

    # 运行分析
    result = analyze_all_stocks(
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        config=Config,
        enable_future_validation=not args.no_future,
        limit=args.limit
    )

    if result:
        logger.info("\n分析成功完成!")
        return 0
    else:
        logger.error("\n分析失败!")
        return 1


if __name__ == "__main__":
    exit(main())
