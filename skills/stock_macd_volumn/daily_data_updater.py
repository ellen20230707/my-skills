"""
每日股票数据更新工具

功能：
1. 每天自动获取当日所有A股的交易数据
2. 追加到现有的股票CSV文件中
3. 避免重复数据
4. 支持定时任务调度（cron）

使用方法：
    python daily_data_updater.py

定时任务配置（每天21:00执行）：
    0 21 * * * cd /Users/ellen_li/2026projects/my-skills/skills/stock_macd_volumn && source ../../venv/bin/activate && python daily_data_updater.py >> logs/daily_update.log 2>&1

Author: Claude
Date: 2026-02-09
"""

import os
import glob
import logging
import pandas as pd
import baostock as bs
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from pathlib import Path

from config import Config


# 配置日志
log_dir = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, 'daily_update.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def get_today_date() -> str:
    """
    获取今天的日期（YYYY-MM-DD格式）

    Returns:
        str: 今天的日期
    """
    return datetime.now().strftime('%Y-%m-%d')


def get_latest_trading_date() -> str:
    """
    获取最近的交易日期（考虑周末和节假日）

    如果今天是周末或节假日，返回上一个交易日的日期

    Returns:
        str: 最近的交易日期
    """
    today = datetime.now()

    # 如果是周六，回退到周五
    if today.weekday() == 5:
        trading_date = today - timedelta(days=1)
    # 如果是周日，回退到周五
    elif today.weekday() == 6:
        trading_date = today - timedelta(days=2)
    else:
        trading_date = today

    return trading_date.strftime('%Y-%m-%d')


def extract_stock_code_from_filename(filename: str) -> Optional[str]:
    """
    从文件名提取股票代码

    文件名格式: sh.600000_浦发银行_近10年日线.csv

    Args:
        filename: CSV文件名

    Returns:
        Optional[str]: 股票代码，如sh.600000
    """
    try:
        # 移除扩展名
        name_part = filename.replace('.csv', '')
        # 分割并提取代码
        parts = name_part.split('_')
        if parts:
            return parts[0]
    except Exception as e:
        logger.error(f"提取股票代码失败: {filename}, {str(e)}")

    return None


def read_existing_csv(file_path: str) -> Tuple[pd.DataFrame, Optional[str]]:
    """
    读取现有的CSV文件，并获取最后一条记录的日期

    Args:
        file_path: CSV文件路径

    Returns:
        Tuple[pd.DataFrame, Optional[str]]: (DataFrame, 最后日期)
    """
    try:
        df = pd.read_csv(file_path)

        if df.empty or 'date' not in df.columns:
            return df, None

        # 获取最后一条记录的日期
        last_date = df.iloc[-1]['date']

        return df, last_date

    except Exception as e:
        logger.error(f"读取CSV失败: {file_path}, {str(e)}")
        return pd.DataFrame(), None


def fetch_daily_data(stock_code: str, date: str, adjustflag: str = "3") -> Optional[pd.DataFrame]:
    """
    从Baostock获取指定日期的股票数据

    Args:
        stock_code: 股票代码，如sh.600000
        date: 日期，YYYY-MM-DD格式
        adjustflag: 复权类型，3=前复权

    Returns:
        Optional[pd.DataFrame]: 当日数据，如果没有交易则返回None
    """
    try:
        rs = bs.query_history_k_data_plus(
            code=stock_code,
            fields="date,open,high,low,close,volume,amount,pctChg",
            start_date=date,
            end_date=date,
            frequency="d",
            adjustflag=adjustflag
        )

        df = rs.get_data()

        if df.empty:
            return None

        # 转换数据类型
        df['open'] = pd.to_numeric(df['open'], errors='coerce')
        df['high'] = pd.to_numeric(df['high'], errors='coerce')
        df['low'] = pd.to_numeric(df['low'], errors='coerce')
        df['close'] = pd.to_numeric(df['close'], errors='coerce')
        df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
        df['pctChg'] = pd.to_numeric(df['pctChg'], errors='coerce')

        return df

    except Exception as e:
        logger.error(f"获取数据失败: {stock_code}, {date}, {str(e)}")
        return None


def append_data_to_csv(file_path: str, new_data: pd.DataFrame) -> bool:
    """
    追加新数据到CSV文件

    Args:
        file_path: CSV文件路径
        new_data: 新数据DataFrame

    Returns:
        bool: 是否成功追加
    """
    try:
        # 追加模式写入，不写入表头
        new_data.to_csv(
            file_path,
            mode='a',
            header=False,
            index=False,
            encoding='utf-8-sig'
        )
        return True

    except Exception as e:
        logger.error(f"追加数据失败: {file_path}, {str(e)}")
        return False


def update_single_stock(file_path: str, target_date: str) -> Tuple[bool, str]:
    """
    更新单只股票的数据

    Args:
        file_path: CSV文件路径
        target_date: 目标日期

    Returns:
        Tuple[bool, str]: (是否成功, 状态消息)
    """
    filename = os.path.basename(file_path)
    stock_code = extract_stock_code_from_filename(filename)

    if not stock_code:
        return False, "无法提取股票代码"

    # 读取现有数据
    existing_df, last_date = read_existing_csv(file_path)

    if last_date is None:
        return False, "无法读取现有数据"

    # 检查是否已有当日数据
    if last_date == target_date:
        return False, f"数据已是最新({target_date})"

    # 获取当日数据
    daily_data = fetch_daily_data(stock_code, target_date)

    if daily_data is None or daily_data.empty:
        return False, f"当日无交易数据"

    # 追加到CSV
    success = append_data_to_csv(file_path, daily_data)

    if success:
        return True, f"成功追加数据({target_date})"
    else:
        return False, "追加数据失败"


def update_all_stocks(data_dir: str = None, target_date: str = None) -> Dict[str, any]:
    """
    更新所有股票的数据

    Args:
        data_dir: 数据目录，默认使用Config.DATA_DIR
        target_date: 目标日期，默认使用最近交易日

    Returns:
        Dict: 更新结果统计
    """
    if data_dir is None:
        data_dir = Config.DATA_DIR

    if target_date is None:
        target_date = get_latest_trading_date()

    logger.info("=" * 60)
    logger.info("每日股票数据更新工具")
    logger.info("=" * 60)
    logger.info(f"数据目录: {data_dir}")
    logger.info(f"目标日期: {target_date}")
    logger.info(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)

    # 登录Baostock
    logger.info("正在登录Baostock...")
    lg = bs.login()
    if lg.error_code != "0":
        logger.error(f"登录失败: {lg.error_msg}")
        return {
            'success': False,
            'error': '登录Baostock失败'
        }

    logger.info("Baostock登录成功")

    # 获取所有CSV文件
    csv_pattern = os.path.join(data_dir, "*.csv")
    csv_files = glob.glob(csv_pattern)

    if not csv_files:
        logger.error(f"未找到CSV文件: {csv_pattern}")
        bs.logout()
        return {
            'success': False,
            'error': '未找到CSV文件'
        }

    logger.info(f"找到 {len(csv_files)} 个股票文件")
    logger.info("开始更新数据...")

    # 统计
    success_count = 0
    already_updated_count = 0
    no_trading_count = 0
    fail_count = 0

    # 遍历更新每只股票
    for i, file_path in enumerate(csv_files, 1):
        filename = os.path.basename(file_path)

        try:
            success, message = update_single_stock(file_path, target_date)

            if success:
                success_count += 1
                logger.debug(f"✓ {filename}: {message}")
            else:
                if "已是最新" in message:
                    already_updated_count += 1
                elif "无交易数据" in message:
                    no_trading_count += 1
                else:
                    fail_count += 1
                    logger.warning(f"⚠ {filename}: {message}")

            # 进度显示（每100只）
            if i % 100 == 0:
                logger.info(f"进度: {i}/{len(csv_files)} | "
                           f"成功: {success_count} | "
                           f"已最新: {already_updated_count} | "
                           f"无交易: {no_trading_count}")

        except Exception as e:
            fail_count += 1
            logger.error(f"✗ {filename}: {str(e)}")

    # 登出
    bs.logout()

    logger.info("=" * 60)
    logger.info("更新完成!")
    logger.info(f"总文件数: {len(csv_files)}")
    logger.info(f"成功更新: {success_count}")
    logger.info(f"已是最新: {already_updated_count}")
    logger.info(f"当日无交易: {no_trading_count}")
    logger.info(f"更新失败: {fail_count}")
    logger.info("=" * 60)

    return {
        'success': True,
        'target_date': target_date,
        'total_files': len(csv_files),
        'success_count': success_count,
        'already_updated_count': already_updated_count,
        'no_trading_count': no_trading_count,
        'fail_count': fail_count
    }


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='每日股票数据更新工具')
    parser.add_argument('--data-dir', help='数据目录路径')
    parser.add_argument('--date', help='指定日期（YYYY-MM-DD），默认为最近交易日')
    parser.add_argument('--test', action='store_true', help='测试模式：只更新前10只股票')

    args = parser.parse_args()

    # 测试模式
    if args.test:
        logger.info("⚠️  测试模式：仅更新前10只股票")
        data_dir = args.data_dir or Config.DATA_DIR
        csv_files = glob.glob(os.path.join(data_dir, "*.csv"))[:10]

        # 临时修改数据目录为测试目录
        test_dir = os.path.join(data_dir, "_test_update")
        os.makedirs(test_dir, exist_ok=True)

        # 复制前10个文件到测试目录
        import shutil
        for f in csv_files:
            shutil.copy(f, test_dir)

        result = update_all_stocks(data_dir=test_dir, target_date=args.date)
    else:
        result = update_all_stocks(data_dir=args.data_dir, target_date=args.date)

    if result['success']:
        logger.info("\n✅ 数据更新成功完成!")
        return 0
    else:
        logger.error(f"\n❌ 数据更新失败: {result.get('error', '未知错误')}")
        return 1


if __name__ == "__main__":
    exit(main())
