"""
Skill名称：数据清洗工具

功能说明：
    提供常用的数据清洗功能，包括处理缺失值、删除重复项、
    标准化列名、识别和处理异常值等。

使用场景：
    - 数据分析前的预处理
    - 原始数据质量检查
    - 批量数据清洗
    - 数据标准化

作者：Your Name
创建日期：2024-02-07
最后更新：2024-02-07
"""

import pandas as pd
import numpy as np
from typing import Optional, Union, List, Dict
import re


def clean_data(
    df: pd.DataFrame,
    drop_duplicates: bool = True,
    handle_missing: str = 'drop',
    standardize_columns: bool = True,
    remove_outliers: bool = False,
    outlier_threshold: float = 3.0
) -> pd.DataFrame:
    """
    综合数据清洗函数，一站式清洗DataFrame
    
    Args:
        df (pd.DataFrame): 需要清洗的数据框
        drop_duplicates (bool): 是否删除重复行. Defaults to True.
        handle_missing (str): 处理缺失值的方式 ('drop', 'fill_mean', 'fill_median', 'fill_zero'). 
                             Defaults to 'drop'.
        standardize_columns (bool): 是否标准化列名. Defaults to True.
        remove_outliers (bool): 是否移除异常值. Defaults to False.
        outlier_threshold (float): 异常值阈值（z-score）. Defaults to 3.0.
    
    Returns:
        pd.DataFrame: 清洗后的数据框
    
    Example:
        >>> df = pd.DataFrame({
        ...     'Name ': ['Alice', 'Bob', 'Alice', 'Charlie'],
        ...     'Age': [25, None, 25, 30],
        ...     'Salary': [50000, 60000, 50000, 200000]
        ... })
        >>> cleaned = clean_data(df, handle_missing='fill_median')
        >>> print(cleaned)
    """
    df_clean = df.copy()
    
    print(f"原始数据: {len(df_clean)} 行, {len(df_clean.columns)} 列")
    
    # 1. 标准化列名
    if standardize_columns:
        df_clean = standardize_column_names(df_clean)
        print("✓ 列名已标准化")
    
    # 2. 删除重复行
    if drop_duplicates:
        before = len(df_clean)
        df_clean = df_clean.drop_duplicates()
        removed = before - len(df_clean)
        if removed > 0:
            print(f"✓ 删除了 {removed} 行重复数据")
    
    # 3. 处理缺失值
    if handle_missing != 'keep':
        df_clean = handle_missing_values(df_clean, method=handle_missing)
        print(f"✓ 缺失值已处理（方法: {handle_missing}）")
    
    # 4. 移除异常值
    if remove_outliers:
        before = len(df_clean)
        df_clean = remove_outliers_zscore(df_clean, threshold=outlier_threshold)
        removed = before - len(df_clean)
        if removed > 0:
            print(f"✓ 移除了 {removed} 行异常值")
    
    print(f"清洗后数据: {len(df_clean)} 行, {len(df_clean.columns)} 列")
    
    return df_clean


def standardize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    标准化列名：转小写、去空格、替换特殊字符为下划线
    
    Args:
        df (pd.DataFrame): 输入数据框
    
    Returns:
        pd.DataFrame: 列名标准化后的数据框
    
    Example:
        >>> df = pd.DataFrame({'Name ': [1], 'Age (years)': [2]})
        >>> df = standardize_column_names(df)
        >>> print(df.columns.tolist())
        ['name', 'age_years']
    """
    df_copy = df.copy()
    
    # 转换列名
    new_columns = []
    for col in df_copy.columns:
        # 转小写
        col_clean = str(col).lower()
        # 去除首尾空格
        col_clean = col_clean.strip()
        # 替换空格和特殊字符为下划线
        col_clean = re.sub(r'[^\w\s]', '_', col_clean)
        col_clean = re.sub(r'\s+', '_', col_clean)
        # 去除连续的下划线
        col_clean = re.sub(r'_+', '_', col_clean)
        # 去除首尾下划线
        col_clean = col_clean.strip('_')
        
        new_columns.append(col_clean)
    
    df_copy.columns = new_columns
    
    return df_copy


def handle_missing_values(
    df: pd.DataFrame, 
    method: str = 'drop',
    columns: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    处理缺失值
    
    Args:
        df (pd.DataFrame): 输入数据框
        method (str): 处理方法 ('drop', 'fill_mean', 'fill_median', 'fill_zero', 'fill_forward')
        columns (List[str], optional): 指定处理的列，None则处理所有列
    
    Returns:
        pd.DataFrame: 处理后的数据框
    
    Raises:
        ValueError: 如果method参数无效
    """
    df_copy = df.copy()
    target_cols = columns if columns else df_copy.columns.tolist()
    
    if method == 'drop':
        df_copy = df_copy.dropna(subset=target_cols)
    
    elif method == 'fill_mean':
        for col in target_cols:
            if df_copy[col].dtype in ['float64', 'int64']:
                df_copy[col].fillna(df_copy[col].mean(), inplace=True)
    
    elif method == 'fill_median':
        for col in target_cols:
            if df_copy[col].dtype in ['float64', 'int64']:
                df_copy[col].fillna(df_copy[col].median(), inplace=True)
    
    elif method == 'fill_zero':
        df_copy[target_cols] = df_copy[target_cols].fillna(0)
    
    elif method == 'fill_forward':
        df_copy[target_cols] = df_copy[target_cols].fillna(method='ffill')
    
    else:
        raise ValueError(f"无效的method: {method}. 可选: 'drop', 'fill_mean', 'fill_median', 'fill_zero', 'fill_forward'")
    
    return df_copy


def remove_outliers_zscore(
    df: pd.DataFrame, 
    threshold: float = 3.0,
    columns: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    使用Z-score方法移除异常值
    
    Args:
        df (pd.DataFrame): 输入数据框
        threshold (float): Z-score阈值，超过此值视为异常. Defaults to 3.0.
        columns (List[str], optional): 指定检查的列，None则检查所有数值列
    
    Returns:
        pd.DataFrame: 移除异常值后的数据框
    
    Example:
        >>> df = pd.DataFrame({'value': [1, 2, 3, 100, 4, 5]})
        >>> df_clean = remove_outliers_zscore(df, threshold=2.0)
        >>> print(len(df_clean))  # 移除了100这个异常值
        5
    """
    df_copy = df.copy()
    
    # 确定要检查的列
    if columns is None:
        numeric_cols = df_copy.select_dtypes(include=[np.number]).columns.tolist()
    else:
        numeric_cols = columns
    
    # 计算Z-score并过滤
    mask = np.ones(len(df_copy), dtype=bool)
    
    for col in numeric_cols:
        if df_copy[col].dtype in ['float64', 'int64']:
            z_scores = np.abs((df_copy[col] - df_copy[col].mean()) / df_copy[col].std())
            mask &= (z_scores <= threshold)
    
    return df_copy[mask]


def get_data_quality_report(df: pd.DataFrame) -> Dict:
    """
    生成数据质量报告
    
    Args:
        df (pd.DataFrame): 输入数据框
    
    Returns:
        Dict: 包含数据质量信息的字典
    
    Example:
        >>> df = pd.DataFrame({'A': [1, 2, None], 'B': [1, 1, 2]})
        >>> report = get_data_quality_report(df)
        >>> print(report['missing_percentage'])
    """
    report = {
        'total_rows': len(df),
        'total_columns': len(df.columns),
        'duplicate_rows': df.duplicated().sum(),
        'missing_values': df.isnull().sum().to_dict(),
        'missing_percentage': (df.isnull().sum() / len(df) * 100).to_dict(),
        'data_types': df.dtypes.to_dict(),
        'memory_usage': df.memory_usage(deep=True).sum() / 1024**2  # MB
    }
    
    return report


def print_quality_report(df: pd.DataFrame) -> None:
    """
    打印格式化的数据质量报告
    
    Args:
        df (pd.DataFrame): 输入数据框
    """
    report = get_data_quality_report(df)
    
    print("=" * 50)
    print("数据质量报告")
    print("=" * 50)
    print(f"总行数: {report['total_rows']}")
    print(f"总列数: {report['total_columns']}")
    print(f"重复行数: {report['duplicate_rows']}")
    print(f"内存使用: {report['memory_usage']:.2f} MB")
    print("\n缺失值统计:")
    print("-" * 50)
    
    for col, missing_count in report['missing_values'].items():
        if missing_count > 0:
            percentage = report['missing_percentage'][col]
            print(f"  {col}: {missing_count} ({percentage:.2f}%)")
    
    print("=" * 50)


# 测试代码
if __name__ == "__main__":
    # 创建测试数据
    test_data = pd.DataFrame({
        'Name ': ['Alice', 'Bob', 'Charlie', 'Alice', 'David'],
        'Age': [25, None, 30, 25, 35],
        'Salary (USD)': [50000, 60000, 200000, 50000, 70000],
        'Department': ['Sales', 'IT', 'IT', 'Sales', None]
    })
    
    print("原始数据:")
    print(test_data)
    print("\n")
    
    # 生成质量报告
    print_quality_report(test_data)
    print("\n")
    
    # 清洗数据
    cleaned_data = clean_data(
        test_data,
        drop_duplicates=True,
        handle_missing='fill_median',
        standardize_columns=True,
        remove_outliers=True,
        outlier_threshold=2.0
    )
    
    print("\n清洗后数据:")
    print(cleaned_data)