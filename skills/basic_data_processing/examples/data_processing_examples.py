"""
数据处理技能使用示例

展示如何使用data_cleaner.py中的各种函数
"""

import sys
sys.path.append('..')  # 添加上级目录到路径

from skills.data_processing.data_cleaner import (
    clean_data,
    standardize_column_names,
    handle_missing_values,
    remove_outliers_zscore,
    print_quality_report
)
import pandas as pd
import numpy as np


def example_1_basic_cleaning():
    """示例1：基础数据清洗流程"""
    print("=" * 60)
    print("示例1：基础数据清洗")
    print("=" * 60)
    
    # 创建示例数据
    df = pd.DataFrame({
        'Employee Name': ['Alice', 'Bob', 'Charlie', 'Alice', 'David'],
        'Age': [25, np.nan, 30, 25, 35],
        'Salary (USD)': [50000, 60000, 200000, 50000, 70000],
        'Department ': ['Sales', 'IT', 'IT', 'Sales', None]
    })
    
    print("原始数据:")
    print(df)
    print()
    
    # 一键清洗
    cleaned = clean_data(
        df,
        drop_duplicates=True,
        handle_missing='fill_median',
        standardize_columns=True
    )
    
    print("\n清洗后数据:")
    print(cleaned)
    print()


def example_2_quality_report():
    """示例2：生成数据质量报告"""
    print("=" * 60)
    print("示例2：数据质量报告")
    print("=" * 60)
    
    # 创建包含各种问题的数据
    df = pd.DataFrame({
        'ID': range(1, 101),
        'Value1': np.random.normal(100, 15, 100),
        'Value2': [np.nan if i % 10 == 0 else np.random.randint(1, 100) for i in range(100)],
        'Category': ['A', 'B', 'C'] * 33 + ['A']
    })
    
    # 添加一些异常值
    df.loc[5, 'Value1'] = 1000
    df.loc[15, 'Value1'] = -500
    
    print_quality_report(df)
    print()


def example_3_custom_cleaning():
    """示例3：自定义清洗步骤"""
    print("=" * 60)
    print("示例3：自定义清洗步骤")
    print("=" * 60)
    
    df = pd.DataFrame({
        'Product Name': ['Item A', 'Item B', 'Item C', 'Item A'],
        'Price ($)': [10.5, None, 15.0, 10.5],
        'Stock': [100, 50, None, 100]
    })
    
    print("原始数据:")
    print(df)
    print()
    
    # 步骤1：标准化列名
    df = standardize_column_names(df)
    print("步骤1 - 标准化列名后:")
    print(df.columns.tolist())
    print()
    
    # 步骤2：只对Price填充均值，Stock填充0
    df = handle_missing_values(df, method='fill_mean', columns=['price'])
    df = handle_missing_values(df, method='fill_zero', columns=['stock'])
    print("步骤2 - 处理缺失值后:")
    print(df)
    print()


def example_4_outlier_removal():
    """示例4：异常值检测和移除"""
    print("=" * 60)
    print("示例4：异常值检测")
    print("=" * 60)
    
    # 创建包含明显异常值的数据
    np.random.seed(42)
    normal_data = np.random.normal(100, 10, 95)
    outliers = [500, 600, -100, -200, 800]
    
    df = pd.DataFrame({
        'ID': range(1, 101),
        'Value': list(normal_data) + outliers
    })
    
    print(f"原始数据统计:")
    print(df['Value'].describe())
    print()
    
    # 移除异常值
    df_clean = remove_outliers_zscore(df, threshold=3.0, columns=['Value'])
    
    print(f"移除异常值后 (threshold=3.0):")
    print(f"保留 {len(df_clean)} 行 (移除了 {len(df) - len(df_clean)} 行)")
    print(df_clean['Value'].describe())
    print()


def example_5_real_world_scenario():
    """示例5：真实场景 - 销售数据清洗"""
    print("=" * 60)
    print("示例5：真实场景 - 销售数据清洗")
    print("=" * 60)
    
    # 模拟真实的销售数据（包含各种问题）
    df = pd.DataFrame({
        'Order ID': [f'ORD{i:04d}' for i in range(1, 21)],
        'Customer Name ': ['Alice', 'Bob', 'Charlie', 'Alice'] * 5,
        'Product': ['Laptop', 'Mouse', 'Keyboard', 'Monitor'] * 5,
        'Quantity': [1, 2, None, 1, 3, 2, 1, None, 2, 1] * 2,
        'Unit Price (USD)': [1000, 25, 50, 300, 1200, 25, 50, 300, 1000, 25] * 2,
        'Discount %': [10, 0, 5, None, 15, 0, 5, 10, 0, None] * 2,
        'Order Date': pd.date_range('2024-01-01', periods=20, freq='D')
    })
    
    # 添加重复订单
    df = pd.concat([df, df.iloc[[0, 5, 10]]], ignore_index=True)
    
    print("原始销售数据问题:")
    print_quality_report(df)
    
    # 清洗数据
    df_clean = clean_data(
        df,
        drop_duplicates=True,
        handle_missing='fill_zero',  # 数量和折扣填0
        standardize_columns=True
    )
    
    # 计算总价
    df_clean['total_price'] = (
        df_clean['quantity'] * 
        df_clean['unit_price_usd'] * 
        (1 - df_clean['discount'] / 100)
    )
    
    print("\n清洗后的数据样例:")
    print(df_clean.head(10))
    print(f"\n总订单数: {len(df_clean)}")
    print(f"总销售额: ${df_clean['total_price'].sum():,.2f}")


if __name__ == "__main__":
    # 运行所有示例
    example_1_basic_cleaning()
    print("\n" * 2)
    
    example_2_quality_report()
    print("\n" * 2)
    
    example_3_custom_cleaning()
    print("\n" * 2)
    
    example_4_outlier_removal()
    print("\n" * 2)
    
    example_5_real_world_scenario()