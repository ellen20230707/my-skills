import baostock as bs
import pandas as pd
import os
from datetime import datetime

# ===================== 配置区 =====================
START_DATE = "2025-01-01"  # 起始日期
END_DATE   = "2026-02-08"  # 结束日期

# 数据保存目录：相对于仓库根目录
# 自动定位到 my-skills/A股近10年日线数据/
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
SAVE_DIR = os.path.join(_REPO_ROOT, "A股近10年日线数据")

ADJUSTFLAG = "3"  # 3=前复权，1=后复权，2=不复权
# ==================================================

# 创建保存目录
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

print(f"数据保存路径: {SAVE_DIR}")

# 登录 Baostock
lg = bs.login()
if lg.error_code != "0":
    print("登录失败:", lg.error_msg)
    exit()
else:
    print("Baostock 登录成功")

# 获取全市场 A 股列表
print("正在获取全市场 A 股列表...")
rs = bs.query_stock_basic()
stock_list = rs.get_data()
# 过滤出正常上市的 A 股
stock_list = stock_list[
    (stock_list["type"] == "1") &  # 1=股票
    (stock_list["status"] == "1")   # 1=正常上市
]
print(f"共获取到 {len(stock_list)} 只 A 股")

# 批量下载日线数据
success_count = 0
fail_count = 0

for idx, row in stock_list.iterrows():
    code = row["code"]
    name = row["code_name"]
    print(f"正在下载: {code} {name} ({idx+1}/{len(stock_list)})")

    try:
        # 查询日线数据
        rs = bs.query_history_k_data_plus(
            code=code,
            fields="date,open,high,low,close,volume,amount,pctChg",
            start_date=START_DATE,
            end_date=END_DATE,
            frequency="d",
            adjustflag=ADJUSTFLAG
        )
        df = rs.get_data()

        if not df.empty:
            # 保存为 CSV
            filename = f"{code}_{name}_近10年日线.csv"
            filepath = os.path.join(SAVE_DIR, filename)
            df.to_csv(filepath, index=False, encoding="utf-8-sig")
            success_count += 1
        else:
            print(f"  ⚠️ {code} {name} 无数据")
            fail_count += 1
    except Exception as e:
        print(f"  ❌ {code} {name} 下载失败: {str(e)}")
        fail_count += 1

# 登出
bs.logout()

print("\n===== 下载完成 =====")
print(f"成功: {success_count} 只")
print(f"失败: {fail_count} 只")
print(f"数据保存在: {os.path.abspath(SAVE_DIR)}")