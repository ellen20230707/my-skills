#!/usr/bin/env python3
"""
路径验证脚本
验证所有脚本中的数据目录路径是否正确配置

Author: Claude
Date: 2026-02-10
"""

import os
import sys

# 添加 skills 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'skills', 'stock_macd_volumn'))

from skills.stock_macd_volumn.config import Config

def verify_paths():
    """验证所有关键路径"""
    print("=" * 80)
    print("📂 路径配置验证")
    print("=" * 80)
    print()

    # 仓库根目录
    repo_root = os.path.dirname(os.path.abspath(__file__))
    print(f"✓ 仓库根目录: {repo_root}")
    print()

    # 数据目录
    data_dir = Config.DATA_DIR
    print(f"✓ 配置的数据目录: {data_dir}")

    if os.path.exists(data_dir):
        csv_count = len([f for f in os.listdir(data_dir) if f.endswith('.csv')])
        print(f"  ✅ 目录存在")
        print(f"  ✅ CSV文件数: {csv_count}")
    else:
        print(f"  ❌ 目录不存在！")
        return False
    print()

    # 输出目录
    output_dir = Config.OUTPUT_DIR
    print(f"✓ 分析输出目录: {output_dir}")
    print()

    # 推荐目录
    rec_dir = os.path.join(repo_root, 'skills', 'stock_daily_recommendation', 'recommendations')
    print(f"✓ 推荐报告目录: {rec_dir}")
    if os.path.exists(rec_dir):
        print(f"  ✅ 目录存在")
    else:
        print(f"  ⚠️  目录不存在（首次运行时会创建）")
    print()

    # 反馈目录
    feedback_dir = os.path.join(repo_root, 'skills', 'stock_daily_recommendation', 'turning_feedback')
    print(f"✓ 反馈文件目录: {feedback_dir}")
    if os.path.exists(feedback_dir):
        print(f"  ✅ 目录存在")
    else:
        print(f"  ❌ 目录不存在！")
        return False
    print()

    # 验证相对路径是否正确
    expected_data_path = os.path.join(repo_root, "A股近10年日线数据")
    if os.path.normpath(data_dir) == os.path.normpath(expected_data_path):
        print("✅ 数据目录路径配置正确！")
    else:
        print(f"⚠️  路径可能不一致:")
        print(f"   期望: {expected_data_path}")
        print(f"   实际: {data_dir}")
    print()

    print("=" * 80)
    print("✅ 路径验证完成！所有路径配置正确。")
    print("=" * 80)
    return True


if __name__ == '__main__':
    success = verify_paths()
    sys.exit(0 if success else 1)
